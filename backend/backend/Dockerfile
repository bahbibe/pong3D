FROM python:3.12.3-alpine3.19

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /backend

COPY ./entrypoint.sh ./entrypoint.sh
COPY ./requirements.txt ./requirements.txt

RUN  pip3 install --disable-pip-version-check --no-cache-dir -r ./requirements.txt 

COPY . .

ENTRYPOINT [ "./entrypoint.sh" ]

CMD [ "python3", "manage.py", "runserver", "0.0.0.0:8000" ]