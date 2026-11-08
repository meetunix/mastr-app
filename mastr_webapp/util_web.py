import io
import logging
import re
import threading
import time
from collections import OrderedDict
from typing import NamedTuple, Optional

import pandas as pd
from requests import RequestException, Session, Response

logger = logging.getLogger(__name__)

# (connect, read) timeout in seconds for all upstream requests; without it a
# stalled upstream would block the worker threads indefinitely
REQUEST_TIMEOUT = (3.05, 30)


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
        r = self.session.get(url, timeout=REQUEST_TIMEOUT)

        if r.status_code != 200:
            raise MastrHTTPQueryException(
                f"Error while GET data from url {url}. HTTP-STATUS: {r.status_code} BODY:{r.text}"
            )
        return r.text

    def __query_head(self, url: str) -> Response:
        r = self.session.head(url, headers={"Accept-Encoding": "identity"}, timeout=REQUEST_TIMEOUT)

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

# A validated entry is reused without asking the upstream again for this long.
# The exports change once a day; this mainly lets threads that waited on the
# per-URL lock reuse the entry the first thread just loaded.
_CSV_FRESH_SECONDS = 60
# Larger CSVs are rejected instead of parsed (the parsed DataFrame needs
# several times the CSV size). The largest table CSV is about 15 MiB.
_CSV_MAX_BYTES = 100 * 1024**2
# Least recently used entries are evicted when the cached DataFrames exceed
# this size (all table CSVs together currently need about 310 MiB).
_CSV_CACHE_MAX_BYTES = 512 * 1024**2


class _CsvEntry(NamedTuple):
    version: Optional[str]  # normalized ETag of the parsed CSV
    df: pd.DataFrame
    nbytes: int
    validated_at: float  # time.monotonic() of the last upstream check


# ETag-validated LRU cache for parsed CSV DataFrames: {url: _CsvEntry}.
# Per-URL locks coalesce concurrent fetches so the upstream isn't hammered
# when several threads miss the same URL simultaneously.
_csv_cache: OrderedDict[str, _CsvEntry] = OrderedDict()
_csv_url_locks: dict[str, threading.Lock] = {}
_csv_meta_lock = threading.Lock()


def _get_csv_url_lock(url: str) -> threading.Lock:
    with _csv_meta_lock:
        lock = _csv_url_locks.get(url)
        if lock is None:
            lock = threading.Lock()
            _csv_url_locks[url] = lock
        return lock


def _cache_get(url: str) -> Optional[_CsvEntry]:
    with _csv_meta_lock:
        entry = _csv_cache.get(url)
        if entry is not None:
            _csv_cache.move_to_end(url)
        return entry


def _cache_put(url: str, entry: _CsvEntry) -> None:
    with _csv_meta_lock:
        _csv_cache[url] = entry
        _csv_cache.move_to_end(url)
        total = sum(e.nbytes for e in _csv_cache.values())
        # the newest entry is always kept, even if it alone exceeds the limit
        while total > _CSV_CACHE_MAX_BYTES and len(_csv_cache) > 1:
            _, evicted = _csv_cache.popitem(last=False)
            total -= evicted.nbytes


def _normalize_etag(etag: Optional[str]) -> Optional[str]:
    """Strip the suffix Apache appends to the ETag of a compressed response
    (mod_deflate: "...-gzip", mod_brotli: "...-br"). Apache does not match
    the suffixed tag in If-None-Match, so it would never answer 304."""
    if etag is None:
        return None
    return re.sub(r'-(gzip|br)"$', '"', etag)


def _read_body(response: Response, url: str) -> bytes:
    """Read the (decoded) response body, refusing bodies above _CSV_MAX_BYTES."""
    message = f"Refusing to load {url}: larger than {_CSV_MAX_BYTES} bytes"
    content_length = response.headers.get("Content-Length", "")
    if content_length.isdigit() and int(content_length) > _CSV_MAX_BYTES:
        raise MastrHTTPQueryException(message)
    body = bytearray()
    for chunk in response.iter_content(chunk_size=1024**2):
        body += chunk
        if len(body) > _CSV_MAX_BYTES:
            raise MastrHTTPQueryException(message)
    return bytes(body)


def cached_read_csv(url: str, max_age: float = _CSV_FRESH_SECONDS) -> tuple[pd.DataFrame, Optional[str]]:
    """Fetch and parse a CSV with ETag-based revalidation.

    Returns the DataFrame and its version (the normalized ETag, None if the
    upstream sends none). All columns are read as text, so values such as
    postcodes with leading zeros are kept exactly as in the CSV.

    An entry validated less than *max_age* seconds ago is returned without
    contacting the upstream. Otherwise a conditional GET (`If-None-Match`) is
    sent; on 304 the cached DataFrame is reused, on 200 the body is
    downloaded once and the cache is replaced. On upstream errors (error
    status, network error, timeout, unparseable body) a stale entry is
    served if one exists, otherwise MastrWebException is raised.
    """
    with _get_csv_url_lock(url):
        cached = _cache_get(url)
        now = time.monotonic()
        if cached is not None and now - cached.validated_at < max_age:
            return cached.df, cached.version

        headers = {"If-None-Match": cached.version} if cached and cached.version else {}
        try:
            with shared_client.session.get(url, headers=headers, timeout=REQUEST_TIMEOUT, stream=True) as response:
                if response.status_code == 304 and cached is not None:
                    _cache_put(url, cached._replace(validated_at=now))
                    return cached.df, cached.version

                if response.status_code != 200:
                    raise MastrHTTPQueryException(
                        f"Error while GET data from url {url}. HTTP-STATUS: {response.status_code} BODY:{response.text}"
                    )

                body = _read_body(response, url)
                version = _normalize_etag(response.headers.get("ETag"))
            df = pd.read_csv(io.BytesIO(body), dtype=str, keep_default_na=False)
        except (
            MastrWebException,
            RequestException,
            pd.errors.ParserError,
            pd.errors.EmptyDataError,
            UnicodeDecodeError,
        ) as e:
            if cached is None:
                if isinstance(e, MastrWebException):
                    raise
                raise MastrHTTPQueryException(f"Error while loading CSV from url {url}: {e}", cause=e) from e
            logger.warning("Serving cached data for %s, upstream failed: %s", url, e)
            # don't retry a failing upstream on every request
            _cache_put(url, cached._replace(validated_at=now))
            return cached.df, cached.version

        _cache_put(url, _CsvEntry(version, df, int(df.memory_usage(deep=True).sum()), now))
        return df, version


def get_dataframe_version(url: str, version: Optional[str]) -> Optional[pd.DataFrame]:
    """Return the DataFrame of *url* in the given *version* (as returned by
    cached_read_csv when the table was loaded).

    The CSV is reloaded if this process has no copy of it, e.g. after a
    restart. Returns None if the upstream file has changed since, because
    row positions in the old version don't apply to the new one. Raises
    MastrWebException if the CSV can't be loaded.
    """
    cached = _cache_get(url)
    if cached is not None and cached.version == version:
        return cached.df
    df, current_version = cached_read_csv(url, max_age=0)
    return df if current_version == version else None


_FILE_SIZE_TTL_SECONDS = 300
_file_size_cache: dict[str, tuple[float, float]] = {}  # {url: (fetched_at, size_mib)}
_file_size_cache_lock = threading.Lock()


def cached_file_size_mib(url: str) -> Optional[float]:
    """File size in MiB, cached for a short time.

    Failed lookups are not cached, so a file that appears later (e.g. the
    database dump after the first pipeline run) is found on the next
    request. The TTL also keeps displayed sizes fresh across pipeline runs.
    """
    now = time.monotonic()
    with _file_size_cache_lock:
        cached = _file_size_cache.get(url)
        if cached is not None and now - cached[0] < _FILE_SIZE_TTL_SECONDS:
            return cached[1]
    file_size = shared_client.get_file_size_mib(url)
    if file_size is not None:
        with _file_size_cache_lock:
            _file_size_cache[url] = (now, file_size)
    return file_size
