from fastapi import Depends, FastAPI, Header, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from html import escape

from pocket_ai.ai.orchestrator import orchestrator
from pocket_ai.core.config import get_config
from pocket_ai.core.onboarding import acknowledge_onboarding, get_onboarding_state
from pocket_ai.core.security import verify_token

app = FastAPI(title="Pocket AI UI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_config().api.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def require_api_client(x_pocket_key: str = Header(default=None)):
    cfg = get_config()
    if not cfg.api.require_auth:
        return
    if not verify_token("api_auth_token", x_pocket_key):
        raise HTTPException(status_code=401, detail="Unauthorized")


class CommandRequest(BaseModel):
    text: str


@app.get("/")
async def root(_: None = Depends(require_api_client)):
    return {"status": "online", "profile": get_config().profile}


@app.post("/command")
async def send_command(cmd: CommandRequest, _: None = Depends(require_api_client)):
    result = await orchestrator.process_text_command(cmd.text)
    return result


@app.get("/config")
async def get_configuration(_: None = Depends(require_api_client)):
    return get_config().model_dump()


@app.get("/onboarding", response_class=HTMLResponse)
async def onboarding_portal(code: str):
    state = get_onboarding_state()
    if not _is_valid_onboarding_state(state, code):
        raise HTTPException(status_code=404, detail="Onboarding not available")
    api_token = state["api_token"]
    mcp_token = state["mcp_token"]
    safe_api = escape(api_token)
    safe_mcp = escape(mcp_token)
    safe_code = escape(code)
    html = f"""
    <html>
    <head>
        <title>Pocket AI Setup</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 640px; margin: 2rem auto; }}
            code {{ background: #f5f5f5; padding: 0.25rem 0.5rem; display: inline-block; }}
            .token {{ margin-bottom: 1rem; }}
            button {{ padding: 0.6rem 1.2rem; }}
        </style>
    </head>
    <body>
        <h1>Welcome to Pocket AI</h1>
        <p>Store these tokens securely—they will disappear after you press "Done".</p>
        <div class="token"><strong>API Token:</strong><br/><code>{safe_api}</code></div>
        <div class="token"><strong>MCP Token:</strong><br/><code>{safe_mcp}</code></div>
        <form method="post" action="/onboarding/ack">
            <input type="hidden" name="code" value="{safe_code}" />
            <button type="submit">Done, hide tokens</button>
        </form>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/onboarding/ack")
async def onboarding_ack(code: str = Form(...)):
    if not acknowledge_onboarding(code):
        raise HTTPException(status_code=400, detail="Invalid or expired setup code")
    return JSONResponse({"status": "ok"})


def _is_valid_onboarding_state(state, code: str) -> bool:
    if not state:
        return False
    if not state.get("pending_ack"):
        return False
    return state.get("setup_code") == code
