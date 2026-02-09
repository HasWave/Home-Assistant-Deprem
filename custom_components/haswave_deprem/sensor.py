"""Sensor platform for HasWave Deprem - son depremler."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SENSOR_DESCRIPTIONS: dict[str, SensorEntityDescription] = {
    "latest": SensorEntityDescription(
        key="latest",
        name="Son Deprem",
        icon="mdi:earthquake",
    ),
    "magnitude": SensorEntityDescription(
        key="magnitude",
        name="Son Deprem Büyüklüğü",
        icon="mdi:gauge",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "max_magnitude": SensorEntityDescription(
        key="max_magnitude",
        name="Maksimum Büyüklük",
        icon="mdi:gauge",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "avg_magnitude": SensorEntityDescription(
        key="avg_magnitude",
        name="Ortalama Büyüklük",
        icon="mdi:gauge",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "count": SensorEntityDescription(
        key="count",
        name="Deprem Sayısı",
        icon="mdi:counter",
        state_class=SensorStateClass.MEASUREMENT,
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Sensor platform kurulumu."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title or "HasWave Deprem",
        manufacturer="HasWave",
    )
    entities = [
        HasWaveDepremSensor(coordinator, desc, key, entry.entry_id, device_info)
        for key, desc in SENSOR_DESCRIPTIONS.items()
    ]
    async_add_entities(entities)


class HasWaveDepremSensor(CoordinatorEntity, SensorEntity):
    """Son depremler ve istatistik sensor'ı."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        description: SensorEntityDescription,
        sensor_key: str,
        entry_id: str,
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._sensor_key = sensor_key
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{sensor_key}"
        self._attr_name = f"Deprem - {description.name}"
        self._attr_device_info = device_info

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    @property
    def native_value(self) -> str | float | int | None:
        earthquakes = self.coordinator.data or []

        if self._sensor_key == "latest":
            if earthquakes:
                latest = earthquakes[0]
                return f"{latest.get('magnitude', 'N/A')} - {latest.get('location', 'N/A')}"
            return "Yok"

        if self._sensor_key == "magnitude":
            if earthquakes:
                return float(earthquakes[0].get("magnitude", 0))
            return 0.0

        if self._sensor_key == "max_magnitude":
            if earthquakes:
                mags = [float(e.get("magnitude", 0)) for e in earthquakes if e.get("magnitude") is not None]
                return max(mags) if mags else 0.0
            return 0.0

        if self._sensor_key == "avg_magnitude":
            if earthquakes:
                mags = [float(e.get("magnitude", 0)) for e in earthquakes if e.get("magnitude") is not None]
                return round(sum(mags) / len(mags), 2) if mags else 0.0
            return 0.0

        if self._sensor_key == "count":
            return len(earthquakes)

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Son deprem listesi ve son deprem detayı."""
        earthquakes = self.coordinator.data or []
        attrs: dict[str, Any] = {}

        if self._sensor_key == "latest" and earthquakes:
            latest = earthquakes[0]
            attrs.update({
                "magnitude": latest.get("magnitude"),
                "location": latest.get("location"),
                "depth": latest.get("depth"),
                "date": latest.get("date"),
                "timestamp": latest.get("timestamp"),
            })

        # Tüm son depremler listesi (son 20)
        if earthquakes:
            attrs["son_depremler"] = [
                {
                    "magnitude": e.get("magnitude"),
                    "location": e.get("location"),
                    "depth": e.get("depth"),
                    "date": e.get("date"),
                    "timestamp": e.get("timestamp"),
                }
                for e in earthquakes[:20]
            ]
        return attrs
