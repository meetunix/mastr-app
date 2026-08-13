import io
import threading
from functools import lru_cache
from typing import Optional

import pandas as pd
from requests import Session, Response


class MastrWebException(Exception):
    def __init__(self, message, cause=None):
        super().__init__(message)
        self.cause = cause


class MastrHTTPQueryException(MastrWebException):
    pass


class RESTClient:
    def __init__(self):
        self.session = Session()

    def query_get(self, url: str) -> str:
        r = self.session.get(url)

        if r.status_code != 200:
            raise MastrHTTPQueryException(
                f"Error while GET data from url {url}. HTTP-STATUS: {r.status_code} BODY:{r.text}"
            )
        return r.text

    def __query_head(self, url: str) -> Response:
        r = self.session.head(url)

        if r.status_code != 200:
            raise MastrHTTPQueryException(
                f"Error while HEAD data from url {url}. HTTP-STATUS: {r.status_code} BODY:{r.text}"
            )
        return r

    def get_file_size_mib(self, url: str) -> Optional[float]:
        try:
            r = self.__query_head(url)
            length = int(r.headers["content-length"])
        except Exception:
            return None
        return length / (1024**2)


# Shared client so cached helpers reuse a single connection pool.
shared_client = RESTClient()

# ETag-validated cache for parsed CSV DataFrames: {url: (etag, dataframe)}.
# Per-URL locks coalesce concurrent fetches so the upstream isn't hammered
# when several threads miss the same URL simultaneously.
_csv_cache: dict[str, tuple[Optional[str], pd.DataFrame]] = {}
_csv_url_locks: dict[str, threading.Lock] = {}
_csv_meta_lock = threading.Lock()


def _get_csv_url_lock(url: str) -> threading.Lock:
    with _csv_meta_lock:
        lock = _csv_url_locks.get(url)
        if lock is None:
            lock = threading.Lock()
            _csv_url_locks[url] = lock
        return lock


def cached_read_csv(url: str) -> pd.DataFrame:
    """Fetch and parse a CSV with ETag-based revalidation.

    Sends a conditional GET (`If-None-Match`). On a hit the server returns
    304 with no body and the cached DataFrame is reused. On a miss the body
    is downloaded once and the cache is replaced. On upstream errors a
    stale entry is served if one exists.
    """
    with _get_csv_url_lock(url):
        cached = _csv_cache.get(url)
        headers = {"If-None-Match": cached[0]} if cached and cached[0] else {}
        response = shared_client.session.get(url, headers=headers)

        if response.status_code == 304 and cached is not None:
            return cached[1]

        if response.status_code != 200:
            if cached is not None:
                return cached[1]
            raise MastrHTTPQueryException(
                f"Error while GET data from url {url}. HTTP-STATUS: {response.status_code} BODY:{response.text}"
            )

        df = pd.read_csv(io.BytesIO(response.content))
        _csv_cache[url] = (response.headers.get("ETag"), df)
        return df


@lru_cache(maxsize=512)
def cached_file_size_mib(url: str) -> Optional[float]:
    return shared_client.get_file_size_mib(url)
