FROM python:3.10

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN set -e; \
    apt-get update ;
    # apt-get -y install netcat ;\
    # apt-get -y install gettext ;

# COPY ./entrypoint.sh /usr/bin/entrypoint.sh

WORKDIR /app

COPY ./requirements.txt ./requirements.txt

RUN set -e; \
    /usr/local/bin/python -m pip install --upgrade pip ;\
    python -m pip install -r ./requirements.txt ;

EXPOSE 8000

# ENTRYPOINT [ "entrypoint.sh" ]

CMD [ "python", "manage.py", "runserver", "0.0.0.0:8000" ]