"""
    Niu Scooter Switch platform for Home Assistant.
    Integrated from custom version B into A.
"""
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    """设置Niu Switch平台。"""
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

    # 添加ACC电源开关
    devices = [
        NiuAccSwitch(hass, api, "acc_on", "acc_off", "ACC Power", api.sn),
    ]

    async_add_entities(devices)
    return True


class NiuAccSwitch(SwitchEntity):
    """代表小牛电动车ACC电源的开关实体。"""
    
    def __init__(self, hass: HomeAssistant, api: NiuApi, turn_on_cmd: str, turn_off_cmd: str, name: str, sn: str) -> None:
        self._hass = hass
        self._api = api
        self._turn_on_cmd = turn_on_cmd
        self._turn_off_cmd = turn_off_cmd
        self._name = f"NIU Scooter {api.sensor_prefix} {name}"
        self._unique_id = f"switch.niu_scooter_{sn}_acc_power"
        self._is_on = False
        self._attr_icon = "mdi:engine" 

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_on(self) -> bool:
        return self._is_on

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, "NIU Scooter - " + self._api.sensor_prefix)},
            "name": "NIU Scooter - " + self._api.sensor_prefix,
            "manufacturer": "NIU",
            "model": self._api.ver,
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """打开开关 (ACC ON)。"""
        success = await self._hass.async_add_executor_job(self._api.send_command, self._turn_on_cmd)
        if success:
            self._is_on = True
            # 发送指令后，强制刷新状态
            await self.async_update() 

    async def async_turn_off(self, **kwargs: Any) -> None:
        """关闭开关 (ACC OFF)。"""
        success = await self._hass.async_add_executor_job(self._api.send_command, self._turn_off_cmd)
        if success:
            self._is_on = False
            await self.async_update()

    async def async_update(self) -> None:
        """更新开关状态。"""
        await self._hass.async_add_executor_job(self._api.updateMoto)
        is_acc_on = self._api.getDataMoto("isAccOn")
        if is_acc_on is not None:
            self._is_on = (is_acc_on == 1)