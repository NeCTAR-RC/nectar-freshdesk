FROM ubuntu:20.04 AS base

RUN apt-get update && apt-get install -y python3 python3-venv netbase
RUN apt-get install -y --no-install-recommends \
            libpython3.$(python3 -c 'import sys; print(sys.version_info.minor);')
RUN python3 -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH

RUN python3 -m pip install -U pip setuptools wheel






FROM base AS build

RUN apt-get update && apt-get install -y python3-dev build-essential

COPY requirements.lock /
RUN mkdir -p /wheels/{deps,app}
RUN python3 -m pip wheel --no-cache-dir --wheel-dir /wheels/deps -r /requirements.lock uwsgi

COPY . /src

RUN python3 -m pip wheel --no-cache-dir --no-deps --wheel-dir /wheels/app /src






FROM base AS run

ARG GID=42424
ARG UID=42424

COPY --from=build /wheels /wheels
COPY requirements.lock /

RUN python3 -m pip install --no-cache-dir --find-links /wheels/deps -r /requirements.lock uwsgi
RUN python3 -m pip install --no-cache-dir  --find-links /wheels/app nectar-freshdesk
RUN python3 -m pip freeze > pip-freeze.txt

RUN rm -rf /wheels

RUN groupadd -g ${GID} nectar-freshdesk
RUN useradd -u ${UID} -g nectar-freshdesk -M -d /var/lib/nectar-freshdesk -s /usr/sbin/nologin -c "nectar-freshdesk user" nectar-freshdesk

RUN mkdir -p /var/lib/nectar-freshdesk /etc/nectar-freshdesk
RUN chown nectar-freshdesk:nectar-freshdesk /etc/nectar-freshdesk /var/lib/nectar-freshdesk
WORKDIR /var/lib/nectar-freshdesk
COPY uwsgi.ini /etc/nectar-freshdesk/

USER ${UID}

CMD ["uwsgi", "--ini", "/etc/nectar-freshdesk/uwsgi.ini"]
