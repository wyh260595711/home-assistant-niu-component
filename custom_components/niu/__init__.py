"""niu component."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_AUTH, CONF_SENSORS, DOMAIN

_LOGGER = logging.getLogger(__name__)

# [修改点] 添加 "switch" 和 "button" 到支持列表
PLATFORMS = ["sensor", "switch", "button"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Niu Smart Plug from a config entry."""

    niu_auth = entry.data.get(CONF_AUTH, None)
    if niu_auth == None:
        return False

    sensors_selected = niu_auth[CONF_SENSORS]
    
    # [修改点] 为了防止因为没选传感器导致开关无法加载，即使没选传感器也允许继续
    if len(sensors_selected) < 1:
        _LOGGER.warning("No sensors selected, but loading integration for controls (Switch/Button).")
        # return False # 注释掉这里，允许仅加载控制功能

    if "LastTrackThumb" in sensors_selected:
        if "camera" not in PLATFORMS:
            PLATFORMS.append("camera")

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    return unload_ok
