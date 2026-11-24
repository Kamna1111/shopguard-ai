"""Small Requests client for talking to the running ShopGuard API."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urljoin

import requests

logger = logging.getLogger(__name__)


class ShopApiClient:
    """Builds consistent HTTP requests without hiding the response from tests."""

    def __init__(self, base_url: str, timeout_seconds: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> requests.Response:
        """Send one request and log its method, path, status, and elapsed time."""
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = self.session.request(
            method=method,
            url=urljoin(f"{self.base_url}/", path.lstrip("/")),
            headers=headers,
            json=json,
            params=params,
            timeout=self.timeout_seconds,
        )
        logger.info(
            "%s %s -> %s (%.0f ms)",
            method.upper(),
            response.request.path_url,
            response.status_code,
            response.elapsed.total_seconds() * 1000,
        )
        return response

    def get(
        self,
        path: str,
        *,
        token: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> requests.Response:
        return self.request("GET", path, token=token, params=params)

    def post(
        self,
        path: str,
        *,
        token: str | None = None,
        json: dict[str, Any] | None = None,
    ) -> requests.Response:
        return self.request("POST", path, token=token, json=json)

    def patch(
        self,
        path: str,
        *,
        token: str | None = None,
        json: dict[str, Any] | None = None,
    ) -> requests.Response:
        return self.request("PATCH", path, token=token, json=json)

    def delete(self, path: str, *, token: str | None = None) -> requests.Response:
        return self.request("DELETE", path, token=token)

    def close(self) -> None:
        self.session.close()
