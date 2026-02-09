"""HasWave Deprem - KOERI kaynağından deprem verisi."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DEFAULT_UPDATE_INTERVAL, DOMAIN
from .api import HasWaveDepremAPI

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Kurulum: KOERI'den veri çeken coordinator + bildirim."""
    all_earthquakes = entry.data.get("all_earthquakes", True)
    city = (entry.data.get("city") or "").strip() if not all_earthquakes else ""
    region = (entry.data.get("region") or "").strip() if not all_earthquakes else ""

    api = HasWaveDepremAPI(
        min_magnitude=float(entry.data.get("min_magnitude", 0.0)),
        limit=int(entry.data.get("limit", 50)),
        city=city,
        region=region,
    )

    update_interval_sec = int(
        entry.options.get("update_interval", entry.data.get("update_interval", DEFAULT_UPDATE_INTERVAL))
    )
    notify_above = float(
        entry.options.get("notify_above_magnitude", entry.data.get("notify_above_magnitude", 4.0))
    )

    # Sadece yeni depremde bildirim: son gördüğümüz en güncel depremin timestamp'i
    last_seen_latest_ts: int = 0

    async def async_update_data():
        nonlocal last_seen_latest_ts
        try:
            data = await hass.async_add_executor_job(api.fetch_earthquakes)
            if data is None:
                return []
            # Yeni deprem: listedeki ilk (en güncel) deprem daha önce gördüğümüzden yeni mi?
            if data and len(data) > 0:
                latest = data[0]
                ts = latest.get("timestamp") or 0
                mag = float(latest.get("magnitude") or 0)
                if mag >= notify_above and ts > last_seen_latest_ts:
                    # İlk çalışmada (last_seen_latest_ts=0) mevcut son deprem için bildirim atma
                    if last_seen_latest_ts > 0:
                        hass.create_task(
                            _send_quake_notification(
                                hass,
                                magnitude=mag,
                                location=latest.get("location", ""),
                                date=latest.get("date", ""),
                                depth=latest.get("depth"),
                            )
                        )
                    last_seen_latest_ts = ts
            return data
        except Exception as err:
            _LOGGER.error("Deprem veri güncelleme hatası: %s", err, exc_info=True)
            return []

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(seconds=update_interval_sec),
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.error("İlk deprem verisi yükleme hatası: %s", err)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "api": api,
        "notify_above_magnitude": notify_above,
    }

    # Options değişince yeniden yükle
    entry.async_on_unload(entry.add_update_listener(_async_update_options))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _send_quake_notification(
    hass: HomeAssistant,
    magnitude: float,
    location: str,
    date: str,
    depth: float | None,
) -> None:
    """Yeni deprem için kalıcı bildirim gönder."""
    try:
        depth_str = f", Derinlik: {depth} km" if depth is not None else ""
        message = f"**{magnitude}** büyüklüğünde deprem\n📍 {location}\n🕐 {date}{depth_str}"
        hass.components.persistent_notification.async_create(
            message,
            title="HasWave Deprem – Yeni Deprem",
            notification_id="haswave_deprem_latest",
        )
    except Exception as e:
        _LOGGER.warning("Deprem bildirimi gönderilemedi: %s", e)


async def _async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Seçenekler değişince entegrasyonu yeniden yükle."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Kaldırma."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
