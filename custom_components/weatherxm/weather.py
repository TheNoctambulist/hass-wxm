"""Weather entities for the WeatherXM integration.

A single weather entity is created for the configured weather station.
"""

import datetime
import zoneinfo
from typing import cast

import pywxm
from homeassistant.components import weather
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .entities import (
    WxmCoordinator,
    WxmCoordinators,
    WxmForecastCoordinator,
    device_info,
)

_MAX_HOURLY_FORECASTS = 48


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    config_entry: ConfigEntry[WxmCoordinators],
    async_add_devices: AddEntitiesCallback,
) -> None:
    """Set up the WeatherXM weather entity."""
    async_add_devices([WxmWeatherEntity(config_entry.runtime_data)])


class WxmWeatherEntity(
    weather.CoordinatorWeatherEntity[
        WxmCoordinator,
        WxmForecastCoordinator,
        WxmForecastCoordinator,
    ]
):
    """Weather entity for a WeatherXM weather station."""

    _attr_has_entity_name = True
    _attr_name = None  # Use the device name
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND

    _attr_supported_features = (
        weather.WeatherEntityFeature.FORECAST_HOURLY
        | weather.WeatherEntityFeature.FORECAST_DAILY
    )

    def __init__(self, coordinators: WxmCoordinators) -> None:
        super().__init__(
            observation_coordinator=coordinators.device,
            daily_coordinator=coordinators.forecast,
            hourly_coordinator=coordinators.forecast,
        )
        self.coordinators = coordinators

        self._attr_unique_id = coordinators.device.data.id
        self._attr_device_info = device_info(coordinators.device.data)

    @property
    def _current_weather(self) -> pywxm.HourlyWeatherData:
        return cast(pywxm.WxmDevice, self.coordinators.device.data).current_weather

    @property
    def _forecast(self) -> pywxm.WeatherForecast:
        return cast(pywxm.WeatherForecast, self.coordinators.forecast.data)

    @property
    def condition(self) -> str | None:  # type: ignore[override] # MyPy doesn't handle these property overrides.
        return _condition_wxm_to_ha(self._current_weather.icon)

    @property
    def humidity(self) -> float | None:  # type: ignore[override]
        return float(self._current_weather.humidity)

    @property
    def native_apparent_temperature(self) -> float | None:  # type: ignore[override]
        return self._current_weather.apparent_temperature

    @property
    def native_dew_point(self) -> float | None:  # type: ignore[override]
        return self._current_weather.dew_point

    @property
    def native_pressure(self) -> float | None:  # type: ignore[override]
        return self._current_weather.absolute_pressure

    @property
    def native_temperature(self) -> float | None:  # type: ignore[override]
        return self._current_weather.temperature

    @property
    def native_wind_gust_speed(self) -> float | None:  # type: ignore[override]
        return self._current_weather.wind_gust

    @property
    def native_wind_speed(self) -> float | None:  # type: ignore[override]
        return self._current_weather.wind_speed

    @property
    def uv_index(self) -> float | None:  # type: ignore[override]
        return float(self._current_weather.uv_index)

    @property
    def wind_bearing(self) -> float | str | None:  # type: ignore[override]
        return self._current_weather.wind_direction

    async def async_forecast_hourly(self) -> list[weather.Forecast] | None:
        # Gather the available hourly forecast data from now for up to 48 hours
        now = dt_util.now()
        hourly_forecasts: list[weather.Forecast] = []
        for f in self._forecast.forecast:
            wxm_hourly_forecasts = f.hourly_forecasts or []
            for hourly_forecast in wxm_hourly_forecasts:
                if (
                    hourly_forecast.timestamp > now
                    and len(hourly_forecasts) < _MAX_HOURLY_FORECASTS
                ):
                    hourly_forecasts.append(_hourly_wxm_to_ha(hourly_forecast))

        return hourly_forecasts

    async def async_forecast_daily(self) -> list[weather.Forecast] | None:
        # Gather the available daily forecast data
        return [
            _daily_wxm_to_ha(
                forecast_timestamp=_to_timestamp(f.forecast_date, f.timezone),
                wxm_forecast=f.daily_forecast,
            )
            for f in self._forecast.forecast
            if f.daily_forecast
        ]


def _condition_wxm_to_ha(icon: str) -> str | None:  # noqa: C901, PLR0911
    """Convert a WeatherXM 'icon' into a Home Assistant condition."""
    if icon in ("clear-day", "extreme-day"):
        return "sunny"
    if icon in ("clear-night", "extreme-night"):
        return "clear-night"
    if icon.startswith("thunderstorms"):
        # All WeatherXM thunderstorm conditions include some degree of rain
        return "lightning-rainy"
    if icon.endswith("extreme-rain"):
        return "pouring"
    if icon.endswith(("drizzle", "rain")):
        return "rainy"
    if icon.endswith("snow"):
        return "snowy"
    if icon.endswith("sleet"):
        return "snowy-rainy"
    # These startswith conditions must be at the bottom since they are more general
    if icon.startswith("partly-cloudy"):
        return "partlycloudy"
    if icon.startswith(("overcast", "cloudy")):
        return "cloudy"
    if icon.startswith(("haze", "fog")):
        return "fog"
    if icon.startswith(("dust", "wind")):
        # Assumes dust is caused by wind...
        return "windy"
    return None


def _hourly_wxm_to_ha(wxm_forecast: pywxm.HourlyForecast) -> weather.Forecast:
    return weather.Forecast(
        datetime=dt_util.as_utc(wxm_forecast.timestamp).isoformat(),
        condition=_condition_wxm_to_ha(wxm_forecast.icon),
        humidity=wxm_forecast.humidity,
        native_apparent_temperature=wxm_forecast.feels_like_temperature,
        native_precipitation=wxm_forecast.precipitation,
        native_pressure=wxm_forecast.pressure,
        native_temperature=wxm_forecast.temperature,
        native_wind_speed=wxm_forecast.wind_speed,
        precipitation_probability=wxm_forecast.precipitation_probability,
        uv_index=wxm_forecast.uv_index,
        wind_bearing=wxm_forecast.wind_direction,
    )


def _to_timestamp(forecast_date: datetime.date, timezone: str) -> datetime.datetime:
    return datetime.datetime.combine(
        forecast_date, datetime.time(), zoneinfo.ZoneInfo(timezone)
    )


def _daily_wxm_to_ha(
    forecast_timestamp: datetime.datetime, wxm_forecast: pywxm.DailyForecast
) -> weather.Forecast:
    return weather.Forecast(
        datetime=forecast_timestamp.astimezone(datetime.UTC).isoformat(),
        condition=_condition_wxm_to_ha(wxm_forecast.icon),
        humidity=wxm_forecast.humidity,
        native_precipitation=wxm_forecast.precipitation_intensity,
        native_pressure=wxm_forecast.pressure,
        native_temperature=wxm_forecast.temperature_max,
        native_templow=wxm_forecast.temperature_min,
        native_wind_speed=wxm_forecast.wind_speed,
        precipitation_probability=wxm_forecast.precipitation_probability,
        uv_index=wxm_forecast.uv_index,
        wind_bearing=wxm_forecast.wind_direction,
    )
