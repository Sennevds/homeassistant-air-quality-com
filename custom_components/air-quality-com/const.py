"""air-quality-com Custom Update Version."""
NAME = "air-quality.com"
VERSION = "1.0.0"
DOMAIN = "air-quality-com"

# Platforms
SENSOR = "sensor"
PLATFORMS = [SENSOR]

CONF_CITY = "conf_city"
CONF_ALLERGENS = "conf_allergens"
CONF_NAME = "conf_name"
CONF_URL = "conf_url"
CONF_LATITUDE = "conf_lat"
CONF_LONGITUDE = "conf_long"
CONF_SPAN_LATITUDE = "conf_span_lat"
CONF_SPAN_LONGITUDE = "conf_span_lon"

STATES = {"i.h.": 0, "L": 1, "L-M": 2, "M": 3, "M-H": 4, "H": 5, "H-H+": 6, "H+": 7}

SENSOR_ICONS = {
    "ar": "mdi:leaf",
    "arte": "mdi:leaf",
    "poac": "mdi:grass",
    "alnu": "mdi:tree",
    "ambr": "mdi:leaf",
    "betu": "mdi:tree",
    "olea": "mdi:tree",
    "default": "mdi:leaf",
}
