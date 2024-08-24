FROM node:20-alpine

RUN apk add --no-cache yarn

WORKDIR /frontend

COPY package.json /frontend
COPY yarn.lock /frontend

RUN yarn install --production=false
# RUN npm install cors

CMD [ "yarn", "dev" ]