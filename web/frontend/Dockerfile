FROM node:22-alpine AS build

WORKDIR /app

ARG VITE_BACKEND_URL
ENV VITE_BACKEND_URL=${VITE_BACKEND_URL}

COPY web/frontend/package.json /app/package.json
COPY web/frontend/package-lock.json /app/package-lock.json
RUN npm ci

COPY web/frontend/index.html /app/index.html
COPY web/frontend/eslint.config.js /app/eslint.config.js
COPY web/frontend/tsconfig.json /app/tsconfig.json
COPY web/frontend/tsconfig.app.json /app/tsconfig.app.json
COPY web/frontend/tsconfig.node.json /app/tsconfig.node.json
COPY web/frontend/vite.config.ts /app/vite.config.ts
COPY web/frontend/src /app/src
RUN npm run build

FROM nginx:1.27-alpine

COPY web/frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
