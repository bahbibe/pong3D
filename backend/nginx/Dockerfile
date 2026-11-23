FROM nginx:alpine

RUN apk update && apk add openssl

COPY ./nginx.conf /etc/nginx/conf.d/nginx.conf

WORKDIR /etc/nginx/ssl

RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout nginx.key -out nginx.crt -subj "/"

CMD ["nginx", "-g", "daemon off;"]

