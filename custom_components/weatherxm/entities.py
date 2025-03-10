"""Utility classes for interacting with the WeatherXM API."""

import datetime
import logging
from dataclasses import dataclass
from typing import cast

import pywxm
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry, update_coordinator
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class WxmCoordinator(update_coordinator.DataUpdateCoordinator[pywxm.WxmDevice]):
    """Co-ordinator to poll the WeatherXM API for device updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry["WxmCoordinators"],
        wxm_api: pywxm.WxmApi,
        device_id: str,
    ) -> None:
        """Initialise the co-ordinator."""
        super().__init__(
            hass=hass,
            config_entry=config_entry,
            logger=_LOGGER,
            name=f"WeatherXM {device_id}",
            update_interval=datetime.timedelta(minutes=5),
            always_update=False,
        )
        self.wxm_api = wxm_api
        self.device_id = device_id

    async def _async_update_data(self) -> pywxm.WxmDevice:
        """Fetch updated weather data."""
        try:
            device_info = await self.wxm_api.get_device(self.device_id)
        except pywxm.AuthenticationError as e:
            raise update_coordinator.ConfigEntryAuthFailed from e
        except pywxm.UnexpectedError as e:
            raise update_coordinator.UpdateFailed(
                f"Error communicating with WeatherXM: {e.message}"
            ) from e
        else:
            _LOGGER.debug("Updated device info: %s", device_info)
            return device_info


class WxmRewardsCoordinator(
    update_coordinator.DataUpdateCoordinator[pywxm.DeviceRewards]
):
    """Co-ordinator to poll the WeatherXM API for device rewards updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry["WxmCoordinators"],
        wxm_api: pywxm.WxmApi,
        device_id: str,
    ) -> None:
        """Initialise the co-ordinator."""
        super().__init__(
            hass=hass,
            config_entry=config_entry,
            logger=_LOGGER,
            name=f"WeatherXM Rewards {device_id}",
            # Rewards data is typically updated once per day, so no need to poll too
            # frequently
            update_interval=datetime.timedelta(minutes=15),
            always_update=False,
        )
        self.wxm_api = wxm_api
        self.device_id = device_id

    async def _async_update_data(self) -> pywxm.DeviceRewards:
        """Fetch updated rewards data."""
        try:
            device_rewards = await self.wxm_api.get_latest_rewards(self.device_id)
        except pywxm.AuthenticationError as e:
            raise update_coordinator.ConfigEntryAuthFailed from e
        except pywxm.UnexpectedError as e:
            raise update_coordinator.UpdateFailed(
                f"Error communicating with WeatherXM: {e.message}"
            ) from e
        else:
            _LOGGER.debug("Updated rewards info: %s", device_rewards)
            return device_rewards


class WxmForecastCoordinator(
    update_coordinator.TimestampDataUpdateCoordinator[pywxm.WeatherForecast]
):
    """Co-ordinator to poll the WeatherXM API for forecast updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry["WxmCoordinators"],
        wxm_api: pywxm.WxmApi,
        device_id: str,
    ) -> None:
        """Initialise the co-ordinator."""
        super().__init__(
            hass=hass,
            config_entry=config_entry,
            logger=_LOGGER,
            name=f"WeatherXM Forecast {device_id}",
            update_interval=datetime.timedelta(minutes=15),
            always_update=False,
        )
        self.wxm_api = wxm_api
        self.device_id = device_id

    async def _async_update_data(self) -> pywxm.WeatherForecast:
        """Fetch updated weather forecasts."""
        try:
            # Aim for up to 8 days of forecast if available
            from_date = dt_util.now().date()
            to_date = from_date + datetime.timedelta(days=7)
            forecast = await self.wxm_api.get_forecast(
                self.device_id,
                from_date=from_date,
                to_date=to_date,
            )
        except pywxm.AuthenticationError as e:
            raise update_coordinator.ConfigEntryAuthFailed from e
        except pywxm.UnexpectedError as e:
            raise update_coordinator.UpdateFailed(
                f"Error communicating with WeatherXM: {e.message}"
            ) from e
        else:
            _LOGGER.debug("Updated weather forecast: %s", forecast)
            return forecast


@dataclass(frozen=True)
class WxmCoordinators:
    """Groups all coordinators so they can be stored in the ConfigEntry runtime data."""

    device: WxmCoordinator
    rewards: WxmRewardsCoordinator
    forecast: WxmForecastCoordinator


class WxmEntity(update_coordinator.CoordinatorEntity[WxmCoordinator]):
    """A mix-in class for common WeatherXM entity logic."""

    # All entities must provide a name
    _attr_has_entity_name = True

    def __init__(self, coordinator: WxmCoordinator, *, id_suffix: str = "") -> None:
        super().__init__(coordinator)

        self._attr_unique_id = coordinator.device_id + id_suffix

        wxm_device: pywxm.WxmDevice = coordinator.data
        self._attr_device_info = device_info(wxm_device)

    @property
    def wxm_device(self) -> pywxm.WxmDevice:
        # Typing for self.coordinator doesn't seem to survive the base class generics.
        return cast(pywxm.WxmDevice, self.coordinator.data)

    @property
    def current_weather(self) -> pywxm.HourlyWeatherData:
        return self.wxm_device.current_weather


class WxmRewardsEntity(update_coordinator.CoordinatorEntity[WxmRewardsCoordinator]):
    """A mix-in class for common WeatherXM Rewards entity logic."""

    # All entities must provide a name
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WxmRewardsCoordinator,
        wxm_device: pywxm.WxmDevice,
        *,
        id_suffix: str,
    ) -> None:
        super().__init__(coordinator)

        self._attr_unique_id = coordinator.device_id + id_suffix
        self._attr_device_info = device_info(wxm_device)

    @property
    def rewards(self) -> pywxm.DeviceRewards:
        # Typing for self.coordinator doesn't seem to survive the base class generics.
        return cast(pywxm.DeviceRewards, self.coordinator.data)


def device_info(device: pywxm.WxmDevice) -> device_registry.DeviceInfo:
    """Return device info for a WeatherXM device."""
    return device_registry.DeviceInfo(
        identifiers={(DOMAIN, device.id)},
        # Prefer the friendly name if it is set.
        name=device.friendly_name or device.name,
        model=device.weather_station_model,
        sw_version=device.firmware_version,
    )
