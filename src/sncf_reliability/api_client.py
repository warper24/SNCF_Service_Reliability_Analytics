"""Transport HTTP borné, avec conservation des tentatives partielles."""

from __future__ import annotations

import hashlib
import http.client
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path


class ApiClient:
    TRANSIENT = {408, 429, 500, 502, 503, 504}

    def __init__(self, *, timeout=60, attempts=3, backoff=2, opener=None, sleep=None):
        if not 0 < timeout <= 120 or not 1 <= attempts <= 5 or not 0 <= backoff <= 10:
            raise ValueError("Paramètres réseau hors des bornes autorisées.")
        self.timeout, self.attempts, self.backoff = timeout, attempts, backoff
        self.opener = opener or urllib.request.urlopen
        self.sleep = sleep or time.sleep

    def download(self, url: str, target: Path, journal) -> dict:
        if target.exists():
            raise FileExistsError(target)
        for number in range(1, self.attempts + 1):
            partial = target.with_name(target.name + f".attempt{number}.partial")
            journal.emit("http_started", url=url, network_attempt=number)
            started = time.monotonic()
            try:
                request = urllib.request.Request(url, headers={
                    "User-Agent": "SNCF-Portfolio-J03/1.0", "Accept-Encoding": "identity",
                })
                with self.opener(request, timeout=self.timeout) as response, partial.open("xb") as out:
                    if response.status != 200:
                        raise urllib.error.HTTPError(url, response.status, "HTTP inattendu", {}, None)
                    length = response.headers.get("Content-Length")
                    size, digest = 0, hashlib.sha256()
                    while chunk := response.read(1024 * 1024):
                        if time.monotonic() - started > self.timeout:
                            raise TimeoutError("Durée totale du téléchargement dépassée.")
                        out.write(chunk)
                        digest.update(chunk)
                        size += len(chunk)
                    if length is not None and size != int(length):
                        raise http.client.IncompleteRead(b"", int(length) - size)
                partial.replace(target)
                result = {"url": url, "bytes": size, "sha256": digest.hexdigest()}
                journal.emit("http_complete", file=target.name, **result)
                return result
            except (urllib.error.URLError, TimeoutError, socket.timeout,
                    ConnectionError, http.client.HTTPException) as error:
                transient = not isinstance(error, urllib.error.HTTPError) or error.code in self.TRANSIENT
                journal.emit("http_error", url=url, network_attempt=number,
                             error_type=type(error).__name__, error=str(error), retryable=transient)
                if not transient or number == self.attempts:
                    raise
                # Retry-After numérique est honoré, mais borné pour garder une reprise limitée.
                delay = self.backoff * 2 ** (number - 1)
                if isinstance(error, urllib.error.HTTPError):
                    retry_after = error.headers.get("Retry-After", "") if error.headers else ""
                    if retry_after.isdigit():
                        delay = max(delay, int(retry_after))
                self.sleep(min(delay, 30))
        raise AssertionError("Boucle de transport terminée sans résultat.")
