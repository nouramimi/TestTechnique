from __future__ import annotations

import logging
import time
from typing import Any, Iterator, Optional

import requests

from ..errors import AuthError, ConnectorError, PermissionDeniedError, RateLimitError

log = logging.getLogger(__name__)

AUTH_CODES = {190, 102}          # token invalide / expiré
PERMISSION_CODES = {10, 200}     # permission manquante
RATE_LIMIT_CODES = {4, 17, 32, 613}


class GraphClient:
    """Petit client HTTP pour l'API Graph : retries, pagination, erreurs typées."""

    def __init__(self, access_token: str, version: str, *, max_retries: int = 3,
                 timeout: float = 15.0, session: Optional[requests.Session] = None):
        self._token = access_token
        self._base = f"https://graph.facebook.com/{version}"
        self._max_retries = max_retries
        self._timeout = timeout
        self._session = session or requests.Session()

    def get(self, path: str, params: Optional[dict] = None) -> dict[str, Any]:
        return self._request(f"{self._base}/{path.lstrip('/')}", dict(params or {}), add_token=True)

    def paginate(self, path: str, params: Optional[dict] = None) -> Iterator[dict[str, Any]]:
        url, query, add_token = f"{self._base}/{path.lstrip('/')}", dict(params or {}), True
        while url:
            payload = self._request(url, query, add_token=add_token)
            yield from payload.get("data", [])
            # l'URL "next" contient déjà les paramètres (dont le token)
            url, query, add_token = payload.get("paging", {}).get("next"), {}, False

    def _request(self, url: str, params: dict, *, add_token: bool) -> dict[str, Any]:
        if add_token:
            params["access_token"] = self._token
        for attempt in range(self._max_retries + 1):
            try:
                resp = self._session.get(url, params=params or None, timeout=self._timeout)
            except requests.RequestException as exc:
                if attempt == self._max_retries:
                    raise ConnectorError(f"Erreur réseau : {type(exc).__name__}") from exc
                self._sleep(attempt)
                continue
            if resp.status_code == 200:
                return resp.json()
            error = self._parse_error(resp)
            code = error.get("code")
            if resp.status_code == 401 or code in AUTH_CODES:
                raise AuthError(error.get("message", "Authentification refusée"))
            if code in PERMISSION_CODES:
                raise PermissionDeniedError(error.get("message", "Permission manquante"))
            if code in RATE_LIMIT_CODES or resp.status_code == 429:
                if attempt == self._max_retries:
                    raise RateLimitError(error.get("message", "Quota dépassé"))
                self._sleep(attempt)
                continue
            if resp.status_code >= 500 and attempt < self._max_retries:
                self._sleep(attempt)
                continue
            raise ConnectorError(f"HTTP {resp.status_code} : {error.get('message', 'erreur inconnue')}")
        raise ConnectorError("Nombre maximal de tentatives atteint")

    @staticmethod
    def _parse_error(resp: requests.Response) -> dict:
        try:
            return resp.json().get("error", {})
        except ValueError:
            return {}

    @staticmethod
    def _sleep(attempt: int) -> None:
        delay = 2 ** attempt
        log.warning("Nouvelle tentative dans %ss", delay)
        time.sleep(delay)
