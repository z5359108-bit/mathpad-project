"""Kalıcı ayarlar: menü üzerinden yönetilir, JSON dosyasına kaydedilir."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, fields
from typing import Any

OUTPUT_MODES = ("latex", "png", "ikisi", "pretty")


@dataclass
class Settings:
    cikti: str = "latex"
    dpi: int = 160
    png_klasor: str = "defter_resim"
    defter_adi: str = "defter"

    @property
    def png_etkin(self) -> bool:
        return self.cikti in {"png", "ikisi"}

    @property
    def latex_etkin(self) -> bool:
        return self.cikti in {"latex", "ikisi"}

    def gecerli(self) -> None:
        if self.cikti not in OUTPUT_MODES:
            self.cikti = "latex"
        try:
            self.dpi = int(self.dpi)
        except (TypeError, ValueError):
            self.dpi = 160
        self.dpi = max(72, min(400, self.dpi))

    @staticmethod
    def load(path: str) -> "Settings":
        data: dict[str, Any] = {}
        try:
            with open(path, encoding="utf-8") as fh:
                loaded = json.load(fh)
            if isinstance(loaded, dict):
                names = {f.name for f in fields(Settings)}
                data = {k: v for k, v in loaded.items() if k in names}
        except (OSError, ValueError):
            data = {}
        settings = Settings(**data)
        settings.gecerli()
        return settings

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(asdict(self), fh, ensure_ascii=False, indent=2)
