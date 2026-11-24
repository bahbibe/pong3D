FROM python:3.12.3-alpine3.19

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /backend

COPY ./entrypoint.sh ./entrypoint.sh
COPY ./requirements.txt ./requirements-dev.txt ./

RUN  pip3 install --disable-pip-version-check --no-cache-dir -r ./requirements.txt

# DEV=1 (compose.dev.yaml) adds the reload tool. Prod and test images skip it.
ARG DEV=0
RUN if [ "$DEV" = "1" ]; then \
        pip3 install --disable-pip-version-check --no-cache-dir -r ./requirements-dev.txt; \
    fi

COPY . .

EXPOSE 8000

ENTRYPOINT [ "./entrypoint.sh" ]

# Prod: daphne without reload, so running games (in memory) are not killed
# by file changes. Dev overrides this command with a reloading one.
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "--proxy-headers", "ft_transcendence.asgi:application"]