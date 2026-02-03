"""
    Niu Scooter Button platform for Home Assistant.
    Integrated from custom version B into A.
"""
import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import NiuApi
from .const import CONF_AUTH, CONF_USERNAME, CONF_PASSWORD, CONF_SCOOTER_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置Niu Button平台。"""
    niu_auth = entry.data.get(CONF_AUTH, None)
    if niu_auth is None:
        return False

    username = niu_auth[CONF_USERNAME]
    password = niu_auth[CONF_PASSWORD]
    scooter_id = niu_auth[CONF_SCOOTER_ID]

    # 初始化 API
    api = NiuApi(username, password, scooter_id)
    try:
        await hass.async_add_executor_job(api.initApi)
    except Exception as e:
        _LOGGER.error(f"初始化Niu API失败: {e}")
        return False

    # 添加坐垫锁按钮
    devices = [
        NiuCushionLockButton(hass, api, "cushion_lock_on", "Cushion Lock", api.sn),
    ]

    async_add_entities(devices)
    return True


class NiuCushionLockButton(ButtonEntity):
    """代表小牛电动车坐垫锁的按钮实体。"""
    
    def __init__(self, hass: HomeAssistant, api: NiuApi, press_cmd: str, name: str, sn: str) -> None:
        self._hass = hass
        self._api = api
        self._press_cmd = press_cmd
        self._name = f"NIU Scooter {api.sensor_prefix} {name}"
        self._unique_id = f"button.niu_scooter_{sn}_cushion_lock"
        self._attr_icon = "mdi:lock-open"

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, "NIU Scooter - " + self._api.sensor_prefix)},
            "name": "NIU Scooter - " + self._api.sensor_prefix,
            "manufacturer": "NIU",
            "model": self._api.ver,
        }

    async def async_press(self) -> None:
        """按下按钮 (打开坐垫)。"""
        await self._hass.async_add_executor_job(self._api.send_command, self._press_cmd)