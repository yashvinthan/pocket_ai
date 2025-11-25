from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Any, Dict, List, Optional

import httpx  # type: ignore[import]

from pocket_ai.core.logger import logger

from .plugin_base import PluginBase, ToolContext


OAUTH_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"
SECRET_KEY = "gmail_token"
DEFAULT_TIMEOUT = 10.0
MAX_SEARCH_RESULTS = 10


class GmailPluginError(Exception):
    """Raised when the Gmail plugin cannot complete the requested action."""


@dataclass
class GmailCredentials:
    access_token: str
    refresh_token: str
    client_id: str
    client_secret: str
    expires_at: datetime
    token_uri: str = OAUTH_TOKEN_ENDPOINT

    @classmethod
    def from_secret(cls, secret_blob: str) -> "GmailCredentials":
        try:
            payload = json.loads(secret_blob)
        except json.JSONDecodeError as exc:
            raise GmailPluginError("Corrupted Gmail OAuth token; please re-link Gmail.") from exc

        missing = {k for k in ["access_token", "refresh_token", "client_id", "client_secret"] if k not in payload}
        if missing:
            raise GmailPluginError(f"Gmail token missing fields: {', '.join(sorted(missing))}")

        expires_at = GmailCredentials._parse_expiry(payload.get("expires_at"))
        return cls(
            access_token=payload["access_token"],
            refresh_token=payload["refresh_token"],
            client_id=payload["client_id"],
            client_secret=payload["client_secret"],
            expires_at=expires_at,
            token_uri=payload.get("token_uri", OAUTH_TOKEN_ENDPOINT),
        )

    @staticmethod
    def _parse_expiry(expires_at: Optional[str]) -> datetime:
        if not expires_at:
            return datetime.now(timezone.utc) - timedelta(seconds=60)
        try:
            normalized = expires_at.replace("Z", "+00:00") if "Z" in expires_at else expires_at
            return datetime.fromisoformat(normalized)
        except ValueError:
            logger.warning("Failed to parse Gmail token expiry, forcing refresh.")
            return datetime.now(timezone.utc) - timedelta(seconds=60)

    @property
    def is_expired(self) -> bool:
        # Refresh slightly before actual expiry to avoid race conditions.
        safety_window = timedelta(seconds=60)
        return datetime.now(timezone.utc) >= (self.expires_at - safety_window)

    def as_secret(self) -> str:
        payload = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "token_uri": self.token_uri,
            "expires_at": self.expires_at.isoformat(),
        }
        return json.dumps(payload)


class GmailPlugin(PluginBase):
    name = "gmail_helper"
    description = "Draft and search emails in Gmail"
    requires_capabilities = ["network", "secrets:gmail_token"]

    def __init__(self) -> None:
        self._timeout = DEFAULT_TIMEOUT

    async def execute(self, input_data: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        try:
            self._guard_policy(context)
        except GmailPluginError as exc:
            return {"status": "error", "message": str(exc)}

        action = (input_data.get("action") or "").strip()
        if not action:
            return {"status": "error", "message": "Action is required."}

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                credentials = await self._get_credentials(context, client)

                if action == "draft_reply":
                    result = await self._draft_reply(input_data, credentials, client)
                elif action == "search_recent":
                    result = await self._search_recent(input_data, credentials, client)
                elif action == "draft_from_last":
                    result = await self._draft_from_last(input_data, credentials, client)
                else:
                    return {"status": "error", "message": f"Unknown action '{action}'."}
        except GmailPluginError as exc:
            return {"status": "error", "message": str(exc)}
        except httpx.RequestError as exc:
            logger.error(f"Gmail network failure: {exc}")
            return {"status": "error", "message": "Network error talking to Gmail. Please retry."}
        except httpx.HTTPStatusError as exc:
            logger.error(f"Gmail API error {exc.response.status_code}: {exc.response.text}")
            return {
                "status": "error",
                "message": f"Gmail API rejected the request ({exc.response.status_code}).",
            }

        return {"status": "success", **result}

    def _guard_policy(self, context: ToolContext) -> None:
        if not context.policy.can_use_cloud(self.name):
            raise GmailPluginError("Cloud access for Gmail is disabled by the current privacy profile.")

        for capability in self.requires_capabilities:
            if not context.policy.can_use_capability(capability, self.name):
                raise GmailPluginError(f"Capability '{capability}' denied for Gmail integration.")

    async def _get_credentials(self, context: ToolContext, client: httpx.AsyncClient) -> GmailCredentials:
        secret_blob = context.secrets.get_secret(SECRET_KEY)
        if not secret_blob:
            raise GmailPluginError("Gmail token is not configured. Run `pocket-cli secrets add gmail_token`.")

        credentials = GmailCredentials.from_secret(secret_blob)
        if credentials.is_expired:
            credentials = await self._refresh_credentials(credentials, context, client)
        return credentials

    async def _refresh_credentials(
        self, credentials: GmailCredentials, context: ToolContext, client: httpx.AsyncClient
    ) -> GmailCredentials:
        logger.info("Refreshing Gmail access token.")
        data = {
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "refresh_token": credentials.refresh_token,
            "grant_type": "refresh_token",
        }
        response = await client.post(credentials.token_uri, data=data)
        response.raise_for_status()
        payload = response.json()

        access_token = payload.get("access_token")
        expires_in = payload.get("expires_in")
        if not access_token or not expires_in:
            raise GmailPluginError("Refresh token response missing required fields.")

        credentials.access_token = access_token
        credentials.expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))

        # Persist the rotated access token securely.
        context.secrets.set_secret(SECRET_KEY, credentials.as_secret())
        return credentials

    @staticmethod
    def _auth_headers(credentials: GmailCredentials) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {credentials.access_token}",
            "Content-Type": "application/json",
        }

    async def _draft_reply(
        self, input_data: Dict[str, Any], credentials: GmailCredentials, client: httpx.AsyncClient
    ) -> Dict[str, Any]:
        to = (input_data.get("to") or "").strip()
        subject = (input_data.get("subject") or "").strip()
        body = (input_data.get("body") or "").strip()
        thread_id = (input_data.get("thread_id") or "").strip()

        if not to or not subject or not body:
            raise GmailPluginError("Draft requests must include 'to', 'subject', and 'body'.")

        message = EmailMessage()
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        if thread_id:
            message["In-Reply-To"] = thread_id

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        payload: Dict[str, Any] = {"message": {"raw": raw_message}}
        if thread_id:
            payload["message"]["threadId"] = thread_id

        response = await client.post(
            f"{GMAIL_API_BASE}/users/me/drafts", headers=self._auth_headers(credentials), json=payload
        )
        response.raise_for_status()
        draft = response.json()

        logger.info("Gmail draft created successfully.")
        return {
            "draft_id": draft.get("id"),
            "thread_id": draft.get("message", {}).get("threadId"),
            "link": "https://mail.google.com/mail/u/0/#drafts",
            "summary": f"Draft for {to} ready in Gmail.",
        }

    async def _search_recent(
        self, input_data: Dict[str, Any], credentials: GmailCredentials, client: httpx.AsyncClient
    ) -> Dict[str, Any]:
        query = (input_data.get("query") or "").strip()
        max_results = min(int(input_data.get("max_results", MAX_SEARCH_RESULTS)), MAX_SEARCH_RESULTS)
        params = {"maxResults": max_results, "labelIds": "INBOX"}
        if query:
            params["q"] = query

        list_resp = await client.get(
            f"{GMAIL_API_BASE}/users/me/messages", headers=self._auth_headers(credentials), params=params
        )
        list_resp.raise_for_status()
        payload = list_resp.json()
        message_refs = payload.get("messages", [])

        messages = await self._hydrate_messages(message_refs, credentials, client)
        return {"emails": messages}

    async def _draft_from_last(
        self, input_data: Dict[str, Any], credentials: GmailCredentials, client: httpx.AsyncClient
    ) -> Dict[str, Any]:
        """Fetch the most recent inbound email and prepare a suggested reply body."""
        query = (input_data.get("query") or "").strip()
        params = {"maxResults": 1, "labelIds": "INBOX", "q": query} if query else {"maxResults": 1, "labelIds": "INBOX"}

        list_resp = await client.get(
            f"{GMAIL_API_BASE}/users/me/messages", headers=self._auth_headers(credentials), params=params
        )
        list_resp.raise_for_status()
        payload = list_resp.json()
        messages = payload.get("messages", [])
        if not messages:
            raise GmailPluginError("No recent emails found to reply to.")

        message_id = messages[0]["id"]
        msg_resp = await client.get(
            f"{GMAIL_API_BASE}/users/me/messages/{message_id}",
            headers=self._auth_headers(credentials),
            params={"format": "metadata", "metadataHeaders": ["Subject", "From"]},
        )
        msg_resp.raise_for_status()
        metadata = msg_resp.json()

        subject = self._extract_header(metadata, "Subject") or "Re: (no subject)"
        sender = self._extract_header(metadata, "From") or "recipient"

        suggested_body = (
            "Hi,\n\n"
            "Thanks for the update — here's my quick response:\n\n"
            "- [Key point]\n- [Next action]\n\n"
            "Let me know if anything needs to change.\n"
            "Thanks,\n"
            "Pocket AI"
        )

        return {
            "thread_id": metadata.get("threadId"),
            "message_id": message_id,
            "subject": subject if subject.lower().startswith("re:") else f"Re: {subject}",
            "to": sender,
            "draft_body": suggested_body,
        }

    async def _hydrate_messages(
        self, messages: List[Dict[str, Any]], credentials: GmailCredentials, client: httpx.AsyncClient
    ) -> List[Dict[str, Any]]:
        hydrated: List[Dict[str, Any]] = []
        for message in messages:
            msg_id = message.get("id")
            if not msg_id:
                continue
            detail_resp = await client.get(
                f"{GMAIL_API_BASE}/users/me/messages/{msg_id}",
                headers=self._auth_headers(credentials),
                params={"format": "metadata", "metadataHeaders": ["Subject", "From", "Date"]},
            )
            detail_resp.raise_for_status()
            data = detail_resp.json()
            hydrated.append(
                {
                    "id": data.get("id"),
                    "thread_id": data.get("threadId"),
                    "subject": self._extract_header(data, "Subject"),
                    "from": self._extract_header(data, "From"),
                    "received_at": self._extract_header(data, "Date"),
                    "snippet": data.get("snippet"),
                }
            )
        return hydrated

    @staticmethod
    def _extract_header(message: Dict[str, Any], header_name: str) -> Optional[str]:
        headers = message.get("payload", {}).get("headers", [])
        for header in headers:
            if header.get("name") == header_name:
                return header.get("value")
        return None
