from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict


class ProfileType(str, Enum):
    OFFLINE_ONLY = "OFFLINE_ONLY"
    HYBRID = "HYBRID"
    CUSTOM = "CUSTOM"


@dataclass(frozen=True)
class ProfileConfig:
    name: ProfileType
    allow_cloud_llm: bool
    allow_cloud_vision: bool
    allow_cloud_speech: bool
    allow_dev_plugins: bool
    logs_enabled: bool


PROFILES: Dict[ProfileType, ProfileConfig] = {
    ProfileType.OFFLINE_ONLY: ProfileConfig(
        name=ProfileType.OFFLINE_ONLY,
        allow_cloud_llm=False,
        allow_cloud_vision=False,
        allow_cloud_speech=False,
        allow_dev_plugins=True,
        logs_enabled=False,
    ),
    ProfileType.HYBRID: ProfileConfig(
        name=ProfileType.HYBRID,
        allow_cloud_llm=True,
        allow_cloud_vision=True,
        allow_cloud_speech=True,
        allow_dev_plugins=True,
        logs_enabled=True,
    ),
    ProfileType.CUSTOM: ProfileConfig(
        name=ProfileType.CUSTOM,
        allow_cloud_llm=False,
        allow_cloud_vision=False,
        allow_cloud_speech=False,
        allow_dev_plugins=True,
        logs_enabled=True,
    ),
}


def get_profile_config(profile_name: str) -> ProfileConfig:
    try:
        return PROFILES[ProfileType(profile_name)]
    except Exception:
        return PROFILES[ProfileType.OFFLINE_ONLY]
