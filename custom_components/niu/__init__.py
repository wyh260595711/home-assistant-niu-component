"""niu component."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_AUTH, CONF_SENSORS, DOMAIN

_LOGGER = logging.getLogger(__name__)

# 支持的平台列表，添加了 "switch", "button" 和 "device_tracker"
PLATFORMS = ["sensor", "switch", "button", "device_tracker"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """从配置条目设置小牛智能插头。"""

    niu_auth = entry.data.get(CONF_AUTH, None)
    if niu_auth is None:
        _LOGGER.error("Niu认证器为空，无法设置集成。")
        return False

    sensors_selected = niu_auth[CONF_SENSORS]
    if len(sensors_selected) < 1:
        _LOGGER.warning("您没有选择任何传感器，集成可能无法完全设置。")
        # 移除 return False，允许即使没有选择传感器也设置集成，因为现在有开关功能
        # return False # 移除此行

    if "LastTrackThumb" in sensors_selected:
        PLATFORMS.append("camera")

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """卸载配置条目。"""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
