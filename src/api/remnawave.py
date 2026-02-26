from remnawave import RemnawaveSDK

from ..utils import get_logger

logger = get_logger("traffic_guard")


class RemnawaveClient:
    def __init__(self, api_url: str, api_token: str, page_size: int = 250):
        self._sdk = RemnawaveSDK(base_url=api_url, token=api_token)
        self._page_size = page_size

    async def close(self):
        await self._sdk._client.aclose()

    async def fetch_all_users(self) -> list[dict]:
        # Raw request instead of sdk.users.get_all_users() to avoid Pydantic
        # validation errors with older panel versions missing required fields.
        all_users: list[dict] = []
        start = 0
        page = 1

        while True:
            try:
                resp = await self._sdk._client.get(
                    "users", params={"start": start, "size": self._page_size},
                )
                resp.raise_for_status()

                body = resp.json()
                data = body.get("response") or body.get("data") or body

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
    ) -> list[dict]:
        try:
            stats = await self._sdk.bandwidthstats.get_stats_user_usage(
                uuid=user_uuid,
                top_nodes_limit=top_nodes_limit,
                start=start_date,
                end=end_date,
            )
            return [
                {
                    "name": node.name,
                    "country_code": node.country_code,
                    "total": node.total,
                }
                for node in stats.response.top_nodes
            ]
        except Exception as e:
            logger.debug(f"Failed to fetch node stats: {e}")
            return []
