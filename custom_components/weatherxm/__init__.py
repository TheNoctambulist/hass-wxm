"""The WeatherXM integration."""

import pywxm
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client

from .const import CONF_DEVICE_ID
from .entities import WxmCoordinator, WxmCoordinators, WxmForecastCoordinator

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.WEATHER,
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry[WxmCoordinators]
) -> bool:
    """Set up the WeatherXM connection."""
    refresh_token = entry.data[CONF_ACCESS_TOKEN]
    device_id = entry.data[CONF_DEVICE_ID]
    wxm_client = pywxm.WxmClient(
        session=aiohttp_client.async_get_clientsession(hass),
        refresh_token=refresh_token,
    )
    wxm_api = pywxm.WxmApi(wxm_client)
    device_coordinator = WxmCoordinator(
        hass=hass,
        config_entry=entry,
        wxm_api=wxm_api,
        device_id=device_id,
    )
    forecast_coordinator = WxmForecastCoordinator(
        hass=hass,
        config_entry=entry,
        wxm_api=wxm_api,
        device_id=device_id,
    )
    entry.runtime_data = WxmCoordinators(device_coordinator, forecast_coordinator)

    # Ensure any changes to the refresh token are persisted.
    async def _async_on_token_update(token: str) -> None:
        """Update the configuration entry whenever the refresh token is updated."""
        new_data = {**entry.data}
        new_data[CONF_ACCESS_TOKEN] = token
        hass.config_entries.async_update_entry(entry, data=new_data)

    await wxm_client.subscribe_refresh_token(_async_on_token_update)

    # Authenticate and load initial weather station data.
    await device_coordinator.async_config_entry_first_refresh()
    await forecast_coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True
