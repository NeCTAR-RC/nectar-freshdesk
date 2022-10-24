FROM python:3.10-alpine AS build

WORKDIR /app
COPY . /app
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"
RUN apk update && apk add --update build-base gcc libc-dev linux-headers && \
    python -m pip install -c https://releases.openstack.org/constraints/upper/zed -r /app/requirements.txt && \
    python -m pip install -c https://releases.openstack.org/constraints/upper/zed .

FROM python:3.10-alpine AS release
COPY --from=build /venv /venv
COPY --from=build /app/docker/docker-run-*.sh /
ENV PYTHONUNBUFFERED=1
ENV PATH="/venv/bin:$PATH"
EXPOSE 8613
USER nobody
