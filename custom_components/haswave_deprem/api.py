"""KOERI'den doğrudan deprem verisi çeker (PHP fetchEarthquakes ile aynı mantık)."""
from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any

import requests

from .const import CITIES, KOERI_URL, REGIONS

_LOGGER = logging.getLogger(__name__)

USER_AGENT = "HasWave-API/1.0"


def _normalize(s: str) -> str:
    """Boşlukları kaldır, büyük harf (PHP uyumlu karşılaştırma)."""
    if not s:
        return ""
    return re.sub(r"\s+", "", s.upper())


def _matches_city(location: str, city: str) -> bool:
    """İl filtresi (PHP matchesCity)."""
    if not city or not location:
        return True
    city_upper = city.strip().upper()
    city_n = _normalize(city_upper)
    loc_n = _normalize(location)
    if city_upper in CITIES:
        return city_n in loc_n or loc_n in city_n
    for il in CITIES:
        il_n = _normalize(il)
        if (il_n in city_n or city_n in il_n) and (il_n in loc_n):
            return True
    return False


def _matches_region(location: str, region: str) -> bool:
    """Bölge filtresi (PHP matchesRegion)."""
    if not region or not location:
        return True
    region_upper = region.strip().upper()
    loc_n = _normalize(location)
    if region_upper in REGIONS:
        for il in REGIONS[region_upper]:
            if _normalize(il) in loc_n:
                return True
        if _normalize(region_upper) in loc_n:
            return True
    return False


def _parse_koeri_content(raw: bytes, limit: int) -> list[dict[str, Any]]:
    """
    KOERI lst0.asp çıktısını parse eder (PHP fetchEarthquakes ile aynı).
    Satır formatı: YYYY.MM.DD HH:MM:SS ... magnitude depth location
    parts[0]=date, [1]=time, [6]=magnitude, [7]=depth, [8:-1]=location
    """
    try:
        text = raw.decode("iso-8859-9", errors="replace")
    except Exception:
        text = raw.decode("utf-8", errors="replace")
    earthquakes: list[dict[str, Any]] = []
    date_re = re.compile(r"\d{4}\.\d{2}\.\d{2}")
    for line in text.splitlines():
        if not date_re.search(line):
            continue
        parts = re.split(r"\s+", line.strip())
        if len(parts) < 8:
            continue
        try:
            date_str = f"{parts[0]} {parts[1]}"
            magnitude = float(parts[6].replace(",", "."))
            depth = float(parts[7].replace(",", "."))
            # PHP: array_slice($parts, 8, -1)
            location = " ".join(parts[8:-1]).strip() if len(parts) > 8 else ""
            if magnitude <= 0 or magnitude > 10:
                continue
            try:
                dt = datetime.strptime(date_str, "%Y.%m.%d %H:%M:%S")
                timestamp = int(dt.timestamp())
            except ValueError:
                timestamp = 0
            earthquakes.append({
                "date": date_str,
                "timestamp": timestamp,
                "magnitude": magnitude,
                "depth": depth,
                "location": location,
            })
        except (ValueError, IndexError):
            continue
        if len(earthquakes) >= limit:
            break
    return earthquakes


class HasWaveDepremAPI:
    """KOERI'den deprem verisi çeker."""

    def __init__(
        self,
        min_magnitude: float = 0.0,
        limit: int = 50,
        city: str = "",
        region: str = "",
    ) -> None:
        self.min_magnitude = min_magnitude
        self.limit = limit
        self.city = (city or "").strip()
        self.region = (region or "").strip()

    def fetch_earthquakes(self) -> list[dict[str, Any]] | None:
        """KOERI lst0.asp'den veri çeker, filtreler ve döndürür."""
        try:
            response = requests.get(
                KOERI_URL,
                timeout=15,
                headers={"User-Agent": USER_AGENT},
            )
            response.raise_for_status()
            raw = response.content
            if not raw:
                _LOGGER.warning("KOERI boş yanıt")
                return []
            # PHP limit'i sonradan uyguluyor; önce yeterince parse edelim
            all_quakes = _parse_koeri_content(raw, limit=500)
            filtered: list[dict[str, Any]] = []
            for eq in all_quakes:
                if eq["magnitude"] < self.min_magnitude:
                    continue
                if self.city and not _matches_city(eq["location"], self.city):
                    continue
                if self.region and not _matches_region(eq["location"], self.region):
                    continue
                filtered.append(eq)
                if len(filtered) >= self.limit:
                    break
            if filtered:
                _LOGGER.info("KOERI: %s deprem alındı", len(filtered))
            else:
                _LOGGER.warning("KOERI: filtreye uyan deprem yok")
            return filtered
        except requests.RequestException as e:
            _LOGGER.error("KOERI bağlantı hatası: %s", e, exc_info=True)
            return None
        except Exception as e:
            _LOGGER.error("KOERI işlem hatası: %s", e, exc_info=True)
            return None
