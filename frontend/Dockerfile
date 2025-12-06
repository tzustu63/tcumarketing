FROM node:18-alpine AS builder

WORKDIR /app

ARG REACT_APP_API_URL=http://localhost:8000

COPY package*.json ./

RUN npm install

COPY . ./

ENV REACT_APP_API_URL=$REACT_APP_API_URL

RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/build /usr/share/nginx/html

COPY start.sh /start.sh
RUN chmod +x /start.sh

ENV PORT=3000
EXPOSE 3000

CMD ["/start.sh"]
