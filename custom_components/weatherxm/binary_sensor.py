"""Binary sensor entities for the WeatherXM integration.

A binary sensor entity is used to publish the batter state for the weather station.
"""

import pywxm
from homeassistant.components import binary_sensor
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entities import WxmCoordinator, WxmCoordinators, WxmEntity


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    config_entry: ConfigEntry[WxmCoordinators],
    async_add_devices: AddEntitiesCallback,
) -> None:
    """Set up the WeatherXM binary sensors."""
    coordinator = config_entry.runtime_data.device

    async_add_devices([WxmBatteryEntity(coordinator)])


class WxmBatteryEntity(WxmEntity, binary_sensor.BinarySensorEntity):
    """Binary sensor reporting the battery state of the weather station."""

    _attr_name = "Battery"
    _attr_device_class = binary_sensor.BinarySensorDeviceClass.BATTERY

    def __init__(self, coordinator: WxmCoordinator) -> None:
        super().__init__(coordinator, id_suffix="_battery")

    @property
    def is_on(self) -> bool | None:  # type: ignore[override] # MyPy can't handle this property override
        return self.wxm_device.battery_state == pywxm.BatteryState.LOW
