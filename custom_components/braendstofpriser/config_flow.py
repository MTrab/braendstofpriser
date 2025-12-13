"""Config flow for braendstofpriser integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.event import async_call_later
from pybraendstofpriser import Braendstofpriser

from . import async_setup_entry, async_unload_entry
from .const import CONF_COMPANY, CONF_PRODUCTS, DOMAIN

_LOGGER = logging.getLogger(__name__)


class BraendstofpriserConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for braendstofpriser."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> BraendstofpriserOptionsFlow:
        """Get the options flow for this handler."""
        return BraendstofpriserOptionsFlow()

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.api: Braendstofpriser = Braendstofpriser()
        self.companies = None
        self._errors = {}
        self.user_input = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        if user_input is None:
            self.companies = await self.api.list_companies()
            # Show the form to the user
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_COMPANY): vol.In(list(self.companies.keys())),
                    }
                ),
            )

        # Process the user input and create the config entry
        self.user_input.update(user_input)
        return await self.async_step_product_selection()

    async def async_step_product_selection(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the product selection step."""
        if user_input is not None:
            p_list = {}
            for product, selected in user_input.items():
                for prod_key, prod_val in self.companies[self.user_input[CONF_COMPANY]][
                    "products"
                ].items():
                    if prod_val["name"] == product:
                        p_list.update({prod_key: selected})

            return self.async_create_entry(
                title=self.user_input[CONF_COMPANY],
                data={"name": self.user_input[CONF_COMPANY]},
                options=p_list,
            )

        # Show the form to the user
        prod_list = list(
            v["name"]
            for _, v in self.companies[self.user_input[CONF_COMPANY]][
                "products"
            ].items()
        )
        schema = {}
        for prod in prod_list:
            schema.update({vol.Required(prod): bool})

        return self.async_show_form(
            step_id="product_selection",
            data_schema=vol.Schema(schema),
        )


class BraendstofpriserOptionsFlow(config_entries.OptionsFlow):
    """Handle a options flow for braendstofpriser."""

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.api: Braendstofpriser = Braendstofpriser()
        self.companies = None
        self._errors = {}
        self.user_input = {}

    async def _do_update(
        self, *args, **kwargs  # pylint: disable=unused-argument
    ) -> None:
        """Update after settings change."""
        await async_unload_entry(self.hass, self.config_entry)
        await async_setup_entry(self.hass, self.config_entry)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        self.companies = await self.api.list_companies()
        if user_input is not None:
            p_list = {}
            for product, selected in user_input.items():
                for prod_key, prod_val in self.companies[self.user_input[CONF_COMPANY]][
                    "products"
                ].items():
                    if prod_val["name"] == product:
                        p_list.update({prod_key: selected})

            async_call_later(self.hass, 2, self._do_update)

            return self.async_create_entry(
                title=self.user_input[CONF_COMPANY],
                data=p_list,
            )

        # Show the form to the user
        company = self.config_entry.data["name"]

        prod_list = list(
            [k, v["name"]] for k, v in self.companies[company]["products"].items()
        )
        schema = {}
        for prod in prod_list:
            schema.update(
                {
                    vol.Required(
                        prod[1], default=self.config_entry.options.get(prod[0], False)
                    ): bool
                }
            )

        self.user_input.update({CONF_COMPANY: company})

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
        )
