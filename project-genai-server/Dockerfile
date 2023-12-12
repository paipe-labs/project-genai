FROM node:20-alpine3.18

WORKDIR /genai-server

COPY package.json .
COPY package-lock.json .

RUN npm install
COPY . .

RUN npm run build

ENTRYPOINT [ "npx", "ts-node", "public/index.js" ]