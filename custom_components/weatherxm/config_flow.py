"""Config flow for the WeatherXM integration."""

from typing import Any

import pywxm
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import aiohttp_client, selector

from .const import CONF_DEVICE_ID, CONF_MINOR_VERSION, CONF_VERSION, DOMAIN

_CONTEXT_WXM_CLIENT = "wxm_client"

_CREDENTIALS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class WxmConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configures the WeatherXM integration."""

    VERSION = CONF_VERSION
    MINOR_VERSION = CONF_MINOR_VERSION

    async def async_step_reauth(
        self, _: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Re-authenticate with WeatherXM."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, data: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if data is None:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=vol.Schema({}),
            )
        return await self.async_step_user()

    async def async_step_user(
        self, data: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initiated by the user."""
        errors: dict[str, str] = {}
        if data is not None:
            wxm_client = pywxm.WxmClient(
                aiohttp_client.async_get_clientsession(self.hass)
            )
            try:
                refresh_token = await wxm_client.login(
                    username=data[CONF_USERNAME],
                    password=data[CONF_PASSWORD],
                )
                self.context[_CONTEXT_WXM_CLIENT] = wxm_client  # type: ignore[literal-required]
                if self.source == config_entries.SOURCE_REAUTH:
                    return self.async_update_reload_and_abort(
                        self._get_reauth_entry(),
                        data_updates={CONF_ACCESS_TOKEN: refresh_token},
                    )
                return await self.async_step_select_device()
            except pywxm.AuthenticationError as e:
                errors[CONF_USERNAME] = e.message

        return self.async_show_form(
            step_id="user", data_schema=_CREDENTIALS_SCHEMA, errors=errors
        )

    async def async_step_select_device(
        self, data: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Select a WeatherXM device to integrate."""
        wxm_client: pywxm.WxmClient = self.context[_CONTEXT_WXM_CLIENT]  # type: ignore[literal-required]
        wxm_api = pywxm.WxmApi(wxm_client)

        if data is not None:
            device_id = data[CONF_DEVICE_ID]
            return await self._async_create_entry_for_device(wxm_api, device_id)

        devices = await wxm_api.list_devices()

        if len(devices) == 1:
            # Automatically register the only device.
            return await self._async_create_entry_for_device(wxm_api, devices[0].id)

        # Otherwise prompt the user to select a weather station.
        device_select_options: list[selector.SelectOptionDict] = [
            {"label": d.friendly_name or d.name, "value": d.id} for d in devices
        ]
        data_schema = vol.Schema(
            {
                vol.Required(CONF_DEVICE_ID): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=device_select_options)
                )
            }
        )
        return self.async_show_form(
            step_id="select_device",
            data_schema=data_schema,
        )

    async def _async_create_entry_for_device(
        self, wxm_api: pywxm.WxmApi, device_id: str
    ) -> config_entries.ConfigFlowResult:
        await self.async_set_unique_id(device_id)
        self._abort_if_unique_id_configured(
            updates={CONF_ACCESS_TOKEN: wxm_api.client.refresh_token}
        )

        device_info = await wxm_api.get_device(device_id)
        return self.async_create_entry(
            title=device_info.name,
            data={
                CONF_ACCESS_TOKEN: wxm_api.client.refresh_token,
                CONF_DEVICE_ID: device_id,
            },
        )
