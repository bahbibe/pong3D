FROM node:20-alpine

WORKDIR /frontend

COPY package.json /frontend
COPY yarn.lock /frontend

RUN yarn install --production=false

EXPOSE 3001

# Plain node: nodemon only restarts server.js, static files are read on
# each request anyway.
CMD [ "node", "server.js" ]