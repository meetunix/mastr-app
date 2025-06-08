from pathlib import Path
from urllib.parse import urlparse, urlunparse

from .constants import EnergySources, DownloadFormats, MASTR_STATIC_EXPORTS_URL, MASTR_STATIC_EXPORTS_PUBLIC_URL


def replace_filetype_on_path(old: str, new_type: str) -> str:
    new_type = new_type if new_type.startswith(".") else "." + new_type
    return str(Path(old).with_suffix(new_type))


def replace_filetype_on_url(url: str, new_type: str) -> str:
    url = urlparse(url)
    url_path = url.path
    new_path_string = replace_filetype_on_path(url_path, new_type)
    url = url._replace(path=new_path_string)
    return str(urlunparse(url))


def to_public_url(url: str) -> str:
    return url.replace(MASTR_STATIC_EXPORTS_URL, MASTR_STATIC_EXPORTS_PUBLIC_URL)


def latinify(input: str) -> str:
    umlauts = [("ä", "ae"), ("ü", "ue"), ("ö", "oe")]
    out = input
    for umlaut in umlauts:
        out = out.replace(umlaut[0], umlaut[1])
        out = out.replace(umlaut[0].capitalize(), umlaut[1].capitalize())
    return out


def get_download_url(source: EnergySources, entity: str, format_type: DownloadFormats) -> str:
    return MASTR_STATIC_EXPORTS_URL + __get_download_url_path(source, entity, format_type)


def get_download_public_url(source: EnergySources, entity: str, format_type: DownloadFormats) -> str:
    return MASTR_STATIC_EXPORTS_PUBLIC_URL + __get_download_url_path(source, entity, format_type)


def __get_download_url_path(source: EnergySources, entity: str, format_type: DownloadFormats) -> str:
    return source.name.lower() + "_" + latinify(entity.lower()) + format_type.value


if __name__ == "__main__":
    print(replace_filetype_on_url("https://example.com/path/to/special.file.type", "toml"))
    print(replace_filetype_on_url("https://example.com/path/to/special", "toml"))
    print(replace_filetype_on_path("/some/file/path/special", "pigz"))
    print(replace_filetype_on_path("/some/file/path/special.gz", "pigz"))
    print("----")
