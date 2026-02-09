"""Config flow for HasWave Deprem integration."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DEFAULT_LIMIT,
    DEFAULT_MIN_MAGNITUDE,
    DEFAULT_NOTIFY_ABOVE_MAGNITUDE,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)
from .api import HasWaveDepremAPI

_LOGGER = logging.getLogger(__name__)


def _load_strings() -> dict:
    """Load strings.json (sync, call from executor in async steps)."""
    strings_path = Path(__file__).parent / "strings.json"
    try:
        with open(strings_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        _LOGGER.warning("Strings yüklenemedi: %s", e)
        return {}


def _get_schema(strings: dict) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required("update_interval", default=DEFAULT_UPDATE_INTERVAL): int,
            vol.Required("limit", default=DEFAULT_LIMIT): vol.All(int, vol.Range(5, 200)),
            vol.Required("min_magnitude", default=DEFAULT_MIN_MAGNITUDE): vol.Coerce(float),
            vol.Required("notify_above_magnitude", default=DEFAULT_NOTIFY_ABOVE_MAGNITUDE): vol.Coerce(float),
            vol.Required("all_earthquakes", default=True): bool,
            vol.Optional("city", default=""): str,
            vol.Optional("region", default=""): str,
        }
    )


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """KOERI'den veri çekerek bağlantıyı doğrula."""
    all_earthquakes = data.get("all_earthquakes", True)
    city = (data.get("city") or "").strip() if not all_earthquakes else ""
    region = (data.get("region") or "").strip() if not all_earthquakes else ""
    api = HasWaveDepremAPI(
        min_magnitude=float(data.get("min_magnitude", DEFAULT_MIN_MAGNITUDE)),
        limit=int(data.get("limit", DEFAULT_LIMIT)),
        city=city,
        region=region,
    )
    result = await hass.async_add_executor_job(api.fetch_earthquakes)
    if result is None:
        raise CannotConnect
    return {"title": "HasWave Deprem"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for HasWave Deprem."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Tek adım: tüm ayarlar."""
        strings = await self.hass.async_add_executor_job(_load_strings)
        error_strings = strings.get("config", {}).get("error", {})

        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=_get_schema(strings),
            )

        errors = {}
        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = error_strings.get("cannot_connect", "cannot_connect")
        except Exception:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = error_strings.get("unknown", "unknown")
        else:
            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_get_schema(strings),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Yapılandır tıklanınca: güncelleme aralığı ve bildirim eşiği."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        d = self._config_entry.data or {}
        opt = self._config_entry.options or {}
        interval = opt.get("update_interval", d.get("update_interval", DEFAULT_UPDATE_INTERVAL))
        try:
            interval = int(interval)
        except (TypeError, ValueError):
            interval = DEFAULT_UPDATE_INTERVAL
        notify = opt.get("notify_above_magnitude", d.get("notify_above_magnitude", DEFAULT_NOTIFY_ABOVE_MAGNITUDE))
        try:
            notify = float(notify)
        except (TypeError, ValueError):
            notify = DEFAULT_NOTIFY_ABOVE_MAGNITUDE
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(
                    "update_interval",
                    default=interval,
                ): vol.In({
                    300: "5 dakika",
                    600: "10 dakika",
                    900: "15 dakika",
                    1800: "30 dakika",
                    3600: "1 saat",
                    14400: "4 saat",
                    86400: "24 saat",
                }),
                vol.Required(
                    "notify_above_magnitude",
                    default=notify,
                ): vol.Coerce(float),
            }),
        )


class CannotConnect(HomeAssistantError):
    """Bağlantı hatası."""
