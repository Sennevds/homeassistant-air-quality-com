import asyncio
import logging
import socket

import aiohttp
import async_timeout

TIMEOUT = 10

_LOGGER: logging.Logger = logging.getLogger(__package__)


class PollenApi:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session
        self._url = "https://air-quality.com/data/get_map_data"

    async def fetch_places(self, post_data: None) -> dict:
        """Get data from the API."""
        post_data["standard"] = "caqi_eu"
        result = await self.api_wrapper("post", self._url, data=post_data)
        return result["data"]["map"]

    async def async_get_data(self, post_data: None) -> dict:
        """Get data from the API."""
        return await self.api_wrapper("post", self._url, data=post_data)

    async def api_wrapper(
        self, method: str, url: str, data: dict = {}, headers: dict = {}
    ) -> dict:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(TIMEOUT):
                if method == "get":
                    response = await self._session.get(url, headers=headers)
                    return await response.json()

                elif method == "put":
                    await self._session.put(url, headers=headers, json=data)

                elif method == "patch":
                    await self._session.patch(url, headers=headers, json=data)

                elif method == "post":
                    response = await self._session.post(url, data=data)
                    json = await response.json(content_type="text/html")
                    return json

        except asyncio.TimeoutError as exception:
            _LOGGER.error(
                "Timeout error fetching information from %s - %s",
                url,
                exception,
            )

        except (KeyError, TypeError) as exception:
            _LOGGER.error(
                "Error parsing information from %s - %s",
                url,
                exception,
            )
        except (aiohttp.ClientError, socket.gaierror) as exception:
            _LOGGER.error(
                "Error fetching information from %s - %s",
                url,
                exception,
            )
        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.error("Something really wrong happened! - %s", exception)
