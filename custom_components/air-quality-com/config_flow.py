import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .api import PollenApi
from homeassistant import config_entries
from .const import (
    DOMAIN,
    CONF_ALLERGENS,
    CONF_NAME,
    CONF_CITY,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_SPAN_LATITUDE,
    CONF_SPAN_LONGITUDE,
)
from homeassistant.helpers.aiohttp_client import async_create_clientsession

_LOGGER: logging.Logger = logging.getLogger(__package__)


class AirQualityComFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Blueprint."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self.data = None
        self.task_fetch_cities = None
        self._init_info = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            try:
                self._init_info["center_lat"] = user_input[CONF_LATITUDE]
                self._init_info["center_lon"] = user_input[CONF_LONGITUDE]
                self._init_info["span_lat"] = user_input[CONF_SPAN_LATITUDE]
                self._init_info["span_lon"] = user_input[CONF_SPAN_LONGITUDE]
                return await self.async_step_fetch_cities(self._init_info)
            except vol.Invalid:
                errors["base"] = "bad_host"

        return self.async_show_form(
            step_id="user",
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_LATITUDE, default=self.hass.config.latitude
                    ): cv.latitude,
                    vol.Optional(
                        CONF_LONGITUDE, default=self.hass.config.longitude
                    ): cv.longitude,
                    vol.Optional(CONF_SPAN_LATITUDE, default=0.02): cv.latitude,
                    vol.Optional(CONF_SPAN_LONGITUDE, default=0.02): cv.longitude,
                }
            ),
        )

    async def async_step_fetch_cities(self, init_info=None):
        if not self.task_fetch_cities:
            self.task_fetch_cities = self.hass.async_create_task(
                self._async_task_fetch_stations(init_info)
            )
            return self.async_show_progress(
                step_id="fetch_cities",
                progress_action="fetch_cities",
            )

        # noinspection PyBroadException
        try:
            await self.task_fetch_cities
        except Exception:  # pylint: disable=broad-except
            return self.async_show_progress_done(next_step_id="fetch_failed")

        if self.data is None:
            return self.async_show_progress_done(next_step_id="fetch_failed")

        return self.async_show_progress_done(next_step_id="select_city")

    async def async_step_fetch_failed(self, user_input=None):
        """Fetching pollen data failed."""
        return self.async_abort(reason="fetch_data_failed")

    async def async_step_select_city(self, user_input=None):
        if user_input is not None:
            self._init_info[CONF_CITY] = user_input[CONF_CITY]
            station = next(
                item
                for item in self.data
                if item["place"]["place_id"] == self._init_info[CONF_CITY]
            )["place"]
            self._init_info[CONF_NAME] = station["name"]
            self._init_info[CONF_LATITUDE] = station["lat"]
            self._init_info[CONF_LONGITUDE] = station["lon"]
            return await self.async_step_select_pollen()

        cities = {
            station["place"][
                "place_id"
            ]: f'{station["place"]["name"]} ({station["place"]["type"]})'
            for station in self.data
        }
        return self.async_show_form(
            step_id="select_city",
            data_schema=vol.Schema(
                {vol.Required(CONF_CITY, default=list(cities.keys())): vol.In(cities)}
            ),
        )

    async def async_step_select_pollen(self, user_input=None):
        if user_input is not None:
            self._init_info[CONF_ALLERGENS] = user_input[CONF_ALLERGENS]
            await self.async_set_unique_id(
                f"{self._init_info[CONF_CITY]}-{self._init_info[CONF_NAME]}"
            )
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=self._init_info[CONF_NAME], data=self._init_info
            )
        station = next(
            item
            for item in self.data
            if item["place"]["place_id"] == self._init_info[CONF_CITY]
        )
        pollen = {
            pollen["kind"]: pollen["name"] for pollen in station["latest"]["readings"]
        }
        return self.async_show_form(
            step_id="select_pollen",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_ALLERGENS, default=list(pollen.keys())
                    ): cv.multi_select(pollen)
                }
            ),
        )

    async def _async_task_fetch_stations(self, init_info=None):
        try:
            session = async_create_clientsession(self.hass)
            client = PollenApi(session)
            self.data = await client.fetch_places(init_info)
            _LOGGER.debug("Fetched data: %s", self.data)
        finally:
            self.hass.async_create_task(
                self.hass.config_entries.flow.async_configure(flow_id=self.flow_id)
            )
