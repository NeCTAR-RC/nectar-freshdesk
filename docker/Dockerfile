FROM python:3.14-slim-trixie AS build

WORKDIR /app
COPY dist/* /app
COPY requirements.txt .
COPY docker/docker-run-*.sh /
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"
RUN apt update && apt install -y build-essential && \
    python -m pip install -c https://releases.openstack.org/constraints/upper/2026.1 -r requirements.txt && \
    python -m pip install -c https://releases.openstack.org/constraints/upper/2026.1 *.tar.gz && rm *.tar.gz
FROM python:3.14-slim-trixie AS release
COPY --from=build /venv /venv
COPY --from=build /docker-run-*.sh /
ENV PYTHONUNBUFFERED=1
ENV PATH="/venv/bin:$PATH"
EXPOSE 8613
USER nobody
