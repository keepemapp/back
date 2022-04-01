FROM python:3.9 as requirements-stage

WORKDIR /tmp

RUN pip install poetry

COPY ./pyproject.toml ./poetry.lock* /tmp/

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# NOT TO USE WITH K8S and other cloud clusters
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

COPY --from=requirements-stage /tmp/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt && mkdir -p /data/assets

HEALTHCHECK CMD curl --fail http://localhost:80/api/v1/health || exit 1

COPY ./kpm /app/kpm
