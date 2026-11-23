FROM python:3.12.3-alpine3.19

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /backend

COPY ./entrypoint.sh ./entrypoint.sh
COPY ./requirements.txt ./requirements.txt

RUN  pip3 install --disable-pip-version-check --no-cache-dir -r ./requirements.txt 

COPY . .

EXPOSE 8000

ENTRYPOINT [ "./entrypoint.sh" ]

# Daphne without autoreload: runserver restarted the process on every file
# change, which killed running games (they live in memory).
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "--proxy-headers", "ft_transcendence.asgi:application"]