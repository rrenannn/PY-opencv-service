from __future__ import annotations

import os
from dataclasses import dataclass

from app.processing import DEFAULT_SHARPNESS_THRESHOLD


@dataclass(frozen=True)
class Settings:
    sharpness_threshold: float = DEFAULT_SHARPNESS_THRESHOLD
    max_upload_size: int = 100 * 1024 * 1024

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            sharpness_threshold=float(
                os.getenv("SHARPNESS_THRESHOLD", str(DEFAULT_SHARPNESS_THRESHOLD))
            ),
            max_upload_size=int(
                os.getenv("MAX_UPLOAD_SIZE", str(100 * 1024 * 1024))
            ),
        )

