FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
COPY yarn.lock ./

RUN yarn install

COPY . .

EXPOSE 5173

CMD ["yarn", "dev", "--host", "0.0.0.0"]
