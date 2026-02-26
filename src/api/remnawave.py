from typing import Any

import aiohttp

from ..utils import get_logger

logger = get_logger("traffic_guard")


class RemnawaveClient:
    def __init__(self, api_url: str, api_token: str, page_size: int = 250):
        self._base_url = api_url.rstrip("/")
        self._token = api_token
        self._page_size = page_size
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self._token}"}
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def fetch_all_users(self) -> list[dict[str, Any]]:
        session = await self._get_session()
        all_users: list[dict] = []
        start = 0
        page = 1

        while True:
            try:
                async with session.get(
                    f"{self._base_url}/users",
                    params={"size": self._page_size, "start": start},
                ) as resp:
                    if resp.status != 200:
                        logger.error(f"API returned status {resp.status}")
                        break

                    result = await resp.json()
                    data = result.get("data") or result.get("response") or result

                    if not data or "users" not in data:
                        break

                    users = data["users"]
                    total = data.get("total", 0)

                    for user in users:
                        traffic = user.get("userTraffic") or {}
                        lifetime_traffic = (
                            user.get("lifetimeUsedTrafficBytes")
                            or traffic.get("lifetimeUsedTrafficBytes")
                            or 0
                        )
                        all_users.append({
                            "uuid": user.get("uuid"),
                            "username": user.get("username"),
                            "telegramId": user.get("telegramId"),
                            "lifetimeUsedTrafficBytes": lifetime_traffic,
                        })

                    logger.info(f"Fetched batch {page}: {len(users)} users ({len(all_users)}/{total})")

                    start += len(users)
                    page += 1

                    if len(users) < self._page_size or start >= total:
                        break

            except Exception as e:
                logger.error(f"Failed to fetch users: {e}")
                break

        return all_users

    async def fetch_user_nodes(
        self,
        user_uuid: str,
        start_date: str,
        end_date: str,
        top_nodes_limit: int = 10,
    ) -> list[dict[str, Any]]:
        session = await self._get_session()

        try:
            async with session.get(
                f"{self._base_url}/bandwidth-stats/users/{user_uuid}",
                params={
                    "topNodesLimit": top_nodes_limit,
                    "start": start_date,
                    "end": end_date,
                },
            ) as resp:
                if resp.status != 200:
                    logger.debug(f"Bandwidth stats returned status {resp.status}")
                    return []

                result = await resp.json()
                data = result.get("response") or result
                top_nodes = data.get("topNodes") or []

                return [
                    {
                        "name": node.get("name", "Unknown"),
                        "country_code": node.get("countryCode", ""),
                        "total": node.get("total", 0),
                    }
                    for node in top_nodes
                ]

        except Exception as e:
            logger.debug(f"Failed to fetch node stats: {e}")
            return []
