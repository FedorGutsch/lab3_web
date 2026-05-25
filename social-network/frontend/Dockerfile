FROM node:20-alpine

WORKDIR /app

ARG REACT_APP_API_URL=http://localhost:8000/api

COPY package.json ./
RUN npm install

COPY . .

# Записываем переменную в .env — react-scripts start гарантированно её прочитает
RUN echo "REACT_APP_API_URL=${REACT_APP_API_URL}" > .env

EXPOSE 3000

CMD ["npm", "start"]
