"""Firecrawl service layer."""

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class FirecrawlService:
    """Service layer for Firecrawl API integration."""

    def __init__(self):
        self.api_key = settings.FIRECRAWL_API_KEY
        self.base_url = settings.FIRECRAWL_BASE_URL
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def create_monitor(
        self,
        name: str,
        url: str,
        schedule: str | None = None,
        goal: str | None = None,
    ) -> dict:
        """Create a Firecrawl monitor."""
        payload = {
            "name": name,
            "targets": [
                {
                    "type": "scrape",
                    "urls": [url],
                    "scrapeOptions": {
                        "formats": ["markdown"],
                    },
                }
            ],
        }

        if schedule:
            payload["schedule"] = {"cron": schedule}
        if goal:
            payload["goal"] = goal

        response = await self.client.post("/v2/monitor", json=payload)
        response.raise_for_status()
        return response.json()

    async def list_monitors(self) -> dict:
        """List all monitors."""
        response = await self.client.get("/v2/monitor")
        response.raise_for_status()
        return response.json()

    async def get_monitor(self, monitor_id: str) -> dict:
        """Get monitor details."""
        response = await self.client.get(f"/v2/monitor/{monitor_id}")
        response.raise_for_status()
        return response.json()

    async def update_monitor(self, monitor_id: str, config: dict) -> dict:
        """Update a monitor."""
        response = await self.client.put(f"/v2/monitor/{monitor_id}", json=config)
        response.raise_for_status()
        return response.json()

    async def delete_monitor(self, monitor_id: str) -> bool:
        """Delete a monitor."""
        response = await self.client.delete(f"/v2/monitor/{monitor_id}")
        response.raise_for_status()
        return True

    async def run_monitor(self, monitor_id: str) -> dict:
        """Run a monitor immediately."""
        response = await self.client.post(f"/v2/monitor/{monitor_id}/run")
        response.raise_for_status()
        return response.json()

    async def list_checks(self, monitor_id: str, limit: int = 25) -> dict:
        """List checks for a monitor."""
        response = await self.client.get(
            f"/v2/monitor/{monitor_id}/checks",
            params={"limit": limit},
        )
        response.raise_for_status()
        return response.json()

    async def get_check(self, monitor_id: str, check_id: str) -> dict:
        """Get check details."""
        response = await self.client.get(f"/v2/monitor/{monitor_id}/checks/{check_id}")
        response.raise_for_status()
        return response.json()

    async def scrape(self, url: str, formats: list = None) -> dict:
        """Scrape a URL on-demand."""
        if formats is None:
            formats = ["markdown"]

        response = await self.client.post(
            "/v2/scrape",
            json={
                "url": url,
                "formats": formats,
                "mobile": True,
            },
        )
        response.raise_for_status()
        return response.json()
