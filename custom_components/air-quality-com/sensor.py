"""
Support for getting current pollen levels
"""

import logging
import json

from collections import namedtuple
from datetime import timedelta
from typing import Any

import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import ENTITY_ID_FORMAT

from dateutil import parser
from datetime import datetime
from .const import VERSION, DOMAIN, SENSOR_ICONS, CONF_CITY, CONF_ALLERGENS, CONF_NAME
from .entity import PollenEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    if not coordinator.data:
        return False

    allergens = {
        pollen["kind"]: pollen["name"]
        for pollen in coordinator.data["latest"]["readings"]
        if pollen["kind"] in entry.data[CONF_ALLERGENS]
    }
    async_add_devices(
        [
            PollenSensor(name, allergen, coordinator, entry)
            for (allergen, name) in allergens.items()
        ]
    )

    return True


class PollenSensor(PollenEntity):
    """Representation of a Pollen sensor."""

    def __init__(self, name, allergen_type, coordinator, config_entry):
        super().__init__(coordinator, config_entry)
        self._allergen_type = allergen_type
        self._name = name
        self.entity_id = ENTITY_ID_FORMAT.format(
            f"pollen_{self.config_entry.data[CONF_NAME]}_{self._allergen_type}"
        )

    @property
    def _allergen(self):
        return next(
            item
            for item in self.coordinator.data.get("latest", []).get("readings", [])
            if item["kind"] == self._allergen_type
        )

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._allergen.get("value", "n/a")

    @property
    def extra_state_attributes(self):
        attributes = {"Level": self._allergen.get("level", "")}
        if hasattr(self, "add_state_attributes"):
            attributes = {**attributes, **self.add_state_attributes}
        return attributes

    @property
    def icon(self):
        """Return the icon for the frontend."""
        return SENSOR_ICONS.get(self._allergen_type, "default")
