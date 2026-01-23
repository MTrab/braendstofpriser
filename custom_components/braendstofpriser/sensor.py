"""Sensor platform for Braendstofpriser integration."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify as util_slugify

from .api import APIClient
from .const import ATTR_COORDINATOR, DOMAIN


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up sensor platform for Braendstofpriser integration."""

    coordinator = hass.data[DOMAIN][entry.entry_id][ATTR_COORDINATOR]

    sensors = []
    for product_key, product_info in coordinator.products.items():
        sensors.append(BraendstofpriserSensor(coordinator, product_key, product_info))

    async_add_devices(sensors, True)


class BraendstofpriserSensor(CoordinatorEntity[APIClient], SensorEntity):
    """Sensor for Braendstofpriser integration."""

    _attr_native_unit_of_measurement = "DKK/L"
    _attr_has_entity_name = True
    _attr_icon = "mdi:gas-station"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, coordinator, product_key, product_info):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._product_key = product_key
        self._product_info = product_info
        self._attr_name = f"{product_info['name']}"
        self._attr_unique_id = util_slugify(
            f"{self.coordinator._last_data['company']['name']}_{self.coordinator._last_data['station']['name']}_{product_key}"
        )

        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    self.coordinator._last_data["company"]["name"],
                    self.coordinator._last_data["station"]["name"],
                )
            },
            name=f"{self.coordinator._last_data['company']['name']} {self.coordinator._last_data['station']['name']}",
            manufacturer=f"{self.coordinator._last_data['company']['name']}, {self.coordinator._last_data['station']['name']}",
            model=product_key,
        )

        self._attr_native_value = self.coordinator.products[self._product_key]["price"]

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        self._attr_native_value = self.coordinator.products[self._product_key]["price"]
        self.async_write_ha_state()
