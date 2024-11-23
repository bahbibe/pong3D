FROM node:20-alpine

RUN apk add --no-cache yarn

WORKDIR /frontend

COPY package.json /frontend
COPY yarn.lock /frontend

RUN yarn install --production=false

EXPOSE 3000

CMD [ "yarn", "dev" ]