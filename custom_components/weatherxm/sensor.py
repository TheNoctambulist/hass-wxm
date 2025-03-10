"""Sensor entities for the WeatherXM integration.

Sensor entities are created for current weather measurements.
"""

from collections.abc import Mapping
from typing import Any

import pywxm
from homeassistant.components import sensor
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    DEGREE,
    PERCENTAGE,
    UnitOfIrradiance,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfVolumetricFlux,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entities import (
    WxmCoordinator,
    WxmCoordinators,
    WxmEntity,
    WxmRewardsCoordinator,
    WxmRewardsEntity,
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    config_entry: ConfigEntry[WxmCoordinators],
    async_add_devices: AddEntitiesCallback,
) -> None:
    """Set up the WeatherXM sensors."""
    device_coordinator = config_entry.runtime_data.device
    rewards_coordinator = config_entry.runtime_data.rewards
    wxm_device: pywxm.WxmDevice = device_coordinator.data

    async_add_devices(
        [
            # Weather entities
            WxmTemperatureEntity(device_coordinator),
            WxmApparentTemperatureEntity(device_coordinator),
            WxmDewPointEntity(device_coordinator),
            WxmHumidityEntity(device_coordinator),
            WxmDailyPrecipitationEntity(device_coordinator),
            WxmPrecipitationRateEntity(device_coordinator),
            WxmWindSpeedEntity(device_coordinator),
            WxmWindGustSpeedEntity(device_coordinator),
            WxmWindDirectionEntity(device_coordinator),
            WxmAbsolutePressure(device_coordinator),
            WxmUvIndexEntity(device_coordinator),
            WxmSolarIrradianceEntity(device_coordinator),
            # Rewards entities
            WxmTotalRewardsEntity(rewards_coordinator, wxm_device),
            WxmLatestRewardEntity(rewards_coordinator, wxm_device),
            WxmDataQualityEntity(rewards_coordinator, wxm_device),
        ]
    )


class WxmTemperatureEntity(WxmEntity, sensor.SensorEntity):
    """Sensor entity reporting the current temperature."""

    _attr_name = "Temperature"
    _attr_device_class = sensor.SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = sensor.SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: WxmCoordinator) -> None:
        super().__init__(coordinator, id_suffix="_temperature")

    @property
    def native_value(self) -> float:  # type: ignore[override] # MyPy can't handle this property override
        return self.current_weather.temperature


class WxmApparentTemperatureEntity(WxmEntity, sensor.SensorEntity):
    """Sensor entity reporting the current apparent (feels-like) temperature."""

    _attr_name = "Apparent Temperature"
    _attr_device_class = sensor.SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = sensor.SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: WxmCoordinator) -> None:
        super().__init__(coordinator, id_suffix="_apparent_temperature")

    @property
    def native_value(self) -> float:  # type: ignore[override] # MyPy can't handle this property override
        return self.current_weather.apparent_temperature


class WxmDewPointEntity(WxmEntity, sensor.SensorEntity):
    """Sensor entity reporting the current dew point."""

    _attr_name = "Dew Point"
    _attr_device_class = sensor.SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = sensor.SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: WxmCoordinator) -> None:
        super().__init__(coordinator, id_suffix="_dew_point")

    @property
    def native_value(self) -> float:  # type: ignore[override] # MyPy can't handle this property override
        return self.current_weather.dew_point


class WxmHumidityEntity(WxmEntity, sensor.SensorEntity):
    """Sensor entity reporting the current humidity."""

    _attr_name = "Humidity"
    _attr_device_class = sensor.SensorDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = sensor.SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: WxmCoordinator) -> None:
        super().__init__(coordinator, id_suffix="_humidity")

    @property
    def native_value(self) -> int:  # type: ignore[override]
        return self.current_weather.humidity


class WxmDailyPrecipitationEntity(WxmEntity, sensor.SensorEntity):
    """Sensor entity reporting the daily rainfall."""

    _attr_name = "Daily Precipitation"
    _attr_device_class = sensor.SensorDeviceClass.PRECIPITATION
    _attr_native_unit_of_measurement = UnitOfPrecipitationDepth.MILLIMETERS
    _attr_state_class = sensor.SensorStateClass.TOTAL_INCREASING
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: WxmCoordinator) -> None:
        super().__init__(coordinator, id_suffix="_precipitation_accumulated")

    @property
    def native_value(self) -> float:  # type: ignore[override]
        return self.current_weather.precipitation_accumulated


class WxmPrecipitationRateEntity(WxmEntity, sensor.SensorEntity):
    """Sensor entity reporting the current precipitation rate."""

    _attr_name = "Precipitation Rate"
    _attr_device_class = sensor.SensorDeviceClass.PRECIPITATION_INTENSITY
    _attr_native_unit_of_measurement = UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR
    _attr_state_class = sensor.SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: WxmCoordinator) -> None:
        super().__init__(coordinator, id_suffix="_precipitation_rate")

    @property
    def native_value(self) -> float:  # type: ignore[override]
        return self.current_weather.precipitation_rate


class WxmWindSpeedEntity(WxmEntity, sensor.SensorEntity):
    """Sensor entity reporting the current wind speed."""

    _attr_name = "Wind Speed"
    _attr_device_class = sensor.SensorDeviceClass.WIND_SPEED
    _attr_native_unit_of_measurement = UnitOfSpeed.METERS_PER_SECOND
    _attr_state_class = sensor.SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: WxmCoordinator) -> None:
        super().__init__(coordinator, id_suffix="_wind_speed")

    @property
    def native_value(self) -> float:  # type: ignore[override]
        return self.current_weather.wind_speed


class WxmWindGustSpeedEntity(WxmEntity, sensor.SensorEntity):
    """Sensor entity reporting the current wind gust speed."""

    _attr_name = "Wind Gust Speed"
    _attr_device_class = sensor.SensorDeviceClass.WIND_SPEED
    _attr_native_unit_of_measurement = UnitOfSpeed.METERS_PER_SECOND
    _attr_state_class = sensor.SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: WxmCoordinator) -> None:
        super().__init__(coordinator, id_suffix="_wind_gust")

    @property
    def native_value(self) -> float:  # type: ignore[override]
        return self.current_weather.wind_gust


class WxmWindDirectionEntity(WxmEntity, sensor.SensorEntity):
    """Sensor entity reporting the originating wind direction."""

    _attr_name = "Wind Direction"
    _attr_device_class = None  # No device class available
    _attr_native_unit_of_measurement = DEGREE
    _attr_state_class = sensor.SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0
    _attr_icon = "mdi:weather-windy"

    def __init__(self, coordinator: WxmCoordinator) -> None:
        super().__init__(coordinator, id_suffix="_wind_direction")

    @property
    def native_value(self) -> float:  # type: ignore[override]
        return self.current_weather.wind_direction


class WxmAbsolutePressure(WxmEntity, sensor.SensorEntity):
    """Sensor entity reporting the absolute air pressure."""

    _attr_name = "Pressure"
    _attr_device_class = sensor.SensorDeviceClass.PRESSURE
    _attr_native_unit_of_measurement = UnitOfPressure.HPA
    _attr_state_class = sensor.SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: WxmCoordinator) -> None:
        super().__init__(coordinator, id_suffix="_absolute_pressure")

    @property
    def native_value(self) -> float:  # type: ignore[override]
        return self.current_weather.absolute_pressure


class WxmUvIndexEntity(WxmEntity, sensor.SensorEntity):
    """Sensor entity reporting the current UV index."""

    _attr_name = "UV Index"
    _attr_device_class = None  # No device class available
    _attr_native_unit_of_measurement = None  # UV Index has no unit
    _attr_state_class = sensor.SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:sun-wireless"

    def __init__(self, coordinator: WxmCoordinator) -> None:
        super().__init__(coordinator, id_suffix="_uv_index")

    @property
    def native_value(self) -> int:  # type: ignore[override]
        return self.current_weather.uv_index


class WxmSolarIrradianceEntity(WxmEntity, sensor.SensorEntity):
    """Sensor entity reporting the current solar irradience."""

    _attr_name = "Solar Irradiance"
    _attr_device_class = sensor.SensorDeviceClass.IRRADIANCE
    _attr_native_unit_of_measurement = UnitOfIrradiance.WATTS_PER_SQUARE_METER
    _attr_state_class = sensor.SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: WxmCoordinator) -> None:
        super().__init__(coordinator, id_suffix="_solar_irradiance")

    @property
    def native_value(self) -> float:  # type: ignore[override]
        return self.current_weather.solar_irradiance


class WxmTotalRewardsEntity(WxmRewardsEntity, sensor.SensorEntity):
    """Sensor entity reporting the total rewards earned."""

    _attr_name = "Total Rewards"
    _attr_state_class = sensor.SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = "WXM"
    _attr_suggested_display_precision = 2
    _attr_icon = "mdi:cash"

    def __init__(
        self, coordinator: WxmRewardsCoordinator, wxm_device: pywxm.WxmDevice
    ) -> None:
        super().__init__(coordinator, wxm_device, id_suffix="_total_rewards")

    @property
    def native_value(self) -> float:  # type: ignore[override]
        return self.rewards.total_rewards


class WxmLatestRewardEntity(WxmRewardsEntity, sensor.SensorEntity):
    """Sensor entity reporting the latest reward earned."""

    _attr_name = "Latest Reward"
    _attr_state_class = sensor.SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "WXM"
    _attr_suggested_display_precision = 2
    _attr_icon = "mdi:cash-plus"

    def __init__(
        self, coordinator: WxmRewardsCoordinator, wxm_device: pywxm.WxmDevice
    ) -> None:
        super().__init__(coordinator, wxm_device, id_suffix="_latest_reward")

    @property
    def native_value(self) -> float:  # type: ignore[override]
        return self.rewards.latest_reward.total_reward

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:  # type: ignore[override]
        return {"reward_time": self.rewards.latest_reward.timestamp}


class WxmDataQualityEntity(WxmRewardsEntity, sensor.SensorEntity):
    """Sensor entity reporting the latest data quality."""

    _attr_name = "Data Quality"
    _attr_state_class = sensor.SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_suggested_display_precision = 0

    def __init__(
        self, coordinator: WxmRewardsCoordinator, wxm_device: pywxm.WxmDevice
    ) -> None:
        super().__init__(coordinator, wxm_device, id_suffix="_data_quality")

    @property
    def native_value(self) -> float:  # type: ignore[override]
        return self.rewards.latest_reward.base_reward_score

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:  # type: ignore[override]
        return {"reward_time": self.rewards.latest_reward.timestamp}
