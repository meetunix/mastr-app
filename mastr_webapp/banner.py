"""Startup banner: once the app answers HTTP requests, a box with its version
and the URLs where it can be reached is printed to stdout.

The URLs are the ones in MASTR_APP_URL (optional, comma-separated: e.g. the
docker port mapping or the ingress host, which the app can't see itself),
followed by the URL the app is served on. Without MASTR_APP_URL, the
container banner shows DEFAULT_CONTAINER_URL (the docker-compose port
mapping) instead.

Only the standard library is used, so the container entrypoint can run it
with the system Python next to Apache:

    python3 banner.py http://127.0.0.1:8080/
"""

import http.client
import os
import socket
import sys
import time
import tomllib
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

READY_TIMEOUT_SECONDS = 120
DEFAULT_CONTAINER_URL = "http://localhost:8081"


def app_version() -> str:
    try:
        with open(Path(__file__).resolve().parent.parent / "pyproject.toml", "rb") as f:
            return tomllib.load(f)["project"]["version"]
    except (OSError, KeyError, tomllib.TOMLDecodeError):
        return "?"


def configured_urls(default: list[str]) -> list[str]:
    urls = [url.strip() for url in os.getenv("MASTR_APP_URL", "").split(",") if url.strip()]
    return urls or default


def format_banner(urls: list[str]) -> str:
    lines = [f"MaStR-App v{app_version()} is running", "", *urls]
    width = max(len(line) for line in lines)
    border = "+" + "-" * (width + 4) + "+"
    return "\n".join([border, *(f"|  {line.ljust(width)}  |" for line in lines), border])


def wait_until_ready(url: str) -> bool:
    """Poll *url* until it answers with 200; False after READY_TIMEOUT_SECONDS."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # never via a proxy
    deadline = time.monotonic() + READY_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        try:
            with opener.open(url, timeout=5) as response:
                if response.status == 200:
                    return True
        except (OSError, http.client.HTTPException):
            # not listening yet, or an error status (e.g. 500 while the app fails to load)
            pass
        time.sleep(1)
    return False


def announce_when_ready(check_url: str, served_url: str, default_urls: list[str] | None = None) -> None:
    """Print the banner once *check_url* answers: the MASTR_APP_URL URLs (or
    *default_urls* if it is not set), then *served_url*."""
    if wait_until_ready(check_url):
        print(format_banner([*configured_urls(default_urls or []), served_url]), flush=True)
    else:
        print(f"MaStR-App did not answer at {check_url} within {READY_TIMEOUT_SECONDS} s", file=sys.stderr, flush=True)


def container_url(port: int) -> str:
    """URL of the app under the container's own address."""
    try:
        address = socket.gethostbyname(socket.gethostname())
    except OSError:
        address = socket.gethostname()
    return f"http://{address}:{port}/ (container)"


if __name__ == "__main__":
    url = sys.argv[1]
    announce_when_ready(url, container_url(urlparse(url).port), [DEFAULT_CONTAINER_URL])
