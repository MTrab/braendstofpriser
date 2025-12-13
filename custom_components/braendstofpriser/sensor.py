"""Sensor platform for Braendstofpriser integration."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .api import APIClient
from .const import ATTR_COORDINATOR, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up sensor platform for Braendstofpriser integration."""

    coordinator = hass.data[DOMAIN][entry.entry_id][ATTR_COORDINATOR]

    sensors = []
    for product_key, product_info in coordinator.products.items():
        sensors.append(BraendstofpriserSensor(coordinator, product_key, product_info))

    async_add_devices(sensors, True)


class BraendstofpriserSensor(CoordinatorEntity[APIClient], SensorEntity):
    """Sensor for Braendstofpriser integration."""

    # _attr_unit_of_measurement = "DKK/L"
    _attr_native_unit_of_measurement = "DKK/L"

    def __init__(self, coordinator, product_key, product_info):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._product_key = product_key
        self._product_info = product_info
        self._attr_name = f"{product_info['name']}"
        self._attr_unique_id = f"{coordinator.company}_{product_key}"
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_icon = "mdi:gas-station"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.company, product_key)},
            "name": self.coordinator.products[self._product_key]["name"],
            "manufacturer": coordinator.company,
            "model": self.coordinator.products[self._product_key]["name"],
        }

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.products[self._product_key]["price"]
