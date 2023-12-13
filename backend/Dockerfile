FROM node:20-alpine3.18

WORKDIR /genai-server

COPY package.json .
COPY yarn.lock .

RUN yarn install
COPY . .

RUN yarn build

ENTRYPOINT [ "npx", "ts-node", "public/index.js" ]