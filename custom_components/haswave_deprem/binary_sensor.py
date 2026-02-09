"""Binary sensor: anlık deprem uyarısı (son deprem eşik üzerindeyse ON)."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Binary sensor platform kurulumu."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    notify_above = hass.data[DOMAIN][entry.entry_id].get("notify_above_magnitude", 4.0)
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title or "HasWave Deprem",
        manufacturer="HasWave",
    )
    entities = [DepremUyariBinarySensor(coordinator, entry.entry_id, notify_above, device_info)]
    async_add_entities(entities)


class DepremUyariBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Son deprem belirtilen büyüklük eşiğinin üzerindeyse ON."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry_id: str,
        notify_above_magnitude: float,
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._notify_above = notify_above_magnitude
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_deprem_uyari"
        self._attr_name = "Deprem uyarısı"
        self._attr_icon = "mdi:earthquake"
        self._attr_device_info = device_info

    @property
    def is_on(self) -> bool:
        """Son deprem eşik üzerindeyse True."""
        earthquakes = self.coordinator.data or []
        if not earthquakes:
            return False
        latest = earthquakes[0]
        mag = latest.get("magnitude")
        if mag is None:
            return False
        try:
            return float(mag) >= self._notify_above
        except (TypeError, ValueError):
            return False

    @property
    def extra_state_attributes(self) -> dict:
        """Son deprem bilgisi."""
        earthquakes = self.coordinator.data or []
        if not earthquakes:
            return {}
        latest = earthquakes[0]
        return {
            "magnitude": latest.get("magnitude"),
            "location": latest.get("location"),
            "depth": latest.get("depth"),
            "date": latest.get("date"),
            "timestamp": latest.get("timestamp"),
        }
