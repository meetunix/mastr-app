FROM debian:12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.7.11 /uv /uvx /bin/

RUN apt-get update && \
    apt-get install -y python3 && \
    apt-get clean

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-editable


FROM debian:12-slim

RUN apt-get update && \
    apt-get install -y apache2 libapache2-mod-wsgi-py3 && \
    apt-get clean

RUN echo "#!/usr/bin/bash" > /apache.sh \
    && echo 'source /etc/apache2/envvars ; exec /usr/sbin/apache2 -DFOREGROUND' >> /apache.sh \
    && chmod +x /apache.sh

RUN mkdir -p /var/run/apache2 \
    && rm -f /etc/apache2/sites-enabled/000-default.conf \
    && echo "LISTEN 8080" > /etc/apache2/ports.conf \
    && sed -ri -e 's!^(\s*ErrorLog)\s+\S+!\1 /proc/self/fd/2!g' /etc/apache2/apache2.conf

COPY conf/apache/vhosts /etc/apache2/sites-enabled/

COPY --from=builder /app /app

ENTRYPOINT ["/apache.sh"]
