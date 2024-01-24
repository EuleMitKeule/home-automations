FROM python:3.11-buster as builder

RUN pip install poetry==1.7.1

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN touch README.md

RUN poetry install --without dev --without test --no-root && rm -rf ${POETRY_CACHE_DIR}

FROM python:3.11-slim-buster as runtime

WORKDIR /app

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY home_automations home_automations

RUN mkdir /config

ENV CONFIG_FILE_PATH=/config/config.yml
ENV LOG_FILE_PATH=/config/home_automations.log

EXPOSE 5000

VOLUME /config
CMD ["python", "-m", "home_automations.__main__"]
