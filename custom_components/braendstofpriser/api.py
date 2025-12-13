"""API for Braendstofpriser integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pybraendstofpriser import Braendstofpriser

from .const import DOMAIN

SCAN_INTERVAL = timedelta(hours=1)

_LOGGER = logging.getLogger(__name__)

type BraendstofpriserConfigEntry = ConfigEntry[APIClient]


class APIClient(DataUpdateCoordinator[None]):
    """DataUpdateCoordinator for Braendstofpriser."""

    def __init__(self, hass, company: str, products) -> None:
        """Initialize the API client."""
        DataUpdateCoordinator.__init__(
            self,
            hass=hass,
            name=DOMAIN,
            logger=_LOGGER,
            update_interval=SCAN_INTERVAL,
        )

        self._api = Braendstofpriser()
        self._hass = hass
        self.company = company
        self._products = products
        self.companies = {}
        self.products = {}

        self.previous_devices: set[str] = set()

    async def initialize(self) -> None:
        """Initialize the API client."""
        self.companies = await self._api.list_companies()
        _LOGGER.debug("Selected products: %s", self._products)
        for product, selected in self._products.items():
            if selected:
                self.products.update(
                    {
                        product: {
                            "name": self.companies[self.company]["products"][product][
                                "name"
                            ],
                            "price": None,
                        }
                    }
                )

    async def _async_update_data(self) -> None:
        """Handle data update request from the coordinator."""

        for product in self.products:
            price = await self._api.get_price(
                company=self.company,
                product=product,
            )
            self.products[product]["price"] = price
            _LOGGER.debug(
                "Updated price for %s %s: %s",
                self.company,
                self.products[product]["name"],
                price,
            )
