FROM python:3.12.3-alpine3.19 AS builder

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHON_DISABLE_PIP_VERSION_CHECK 1

WORKDIR /backend

COPY ./entrypoint.sh ./entrypoint.sh
COPY ./requirements.txt ./requirements.txt

RUN  python -m pip install -r ./requirements.txt 

FROM builder AS dev

COPY --from=builder /backend /backend

ENTRYPOINT [ "./entrypoint.sh" ]

CMD [ "python", "manage.py", "runserver", "0.0.0.0:8000" ]