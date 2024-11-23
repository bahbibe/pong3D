FROM nginx:alpine

COPY ./nginx.conf /etc/nginx/conf.d/nginx.conf

COPY  ./ssl/nginx.crt /etc/nginx/ssl/nginx.crt
COPY  ./ssl/nginx.key /etc/nginx/ssl/nginx.key

CMD ["nginx", "-g", "daemon off;"]

