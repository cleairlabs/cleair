FROM python:3.11-slim AS build

WORKDIR /app

ARG DOCS_DOMAIN

COPY docs/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY docs /app/docs
RUN DOCS_SITE_URL="https://${DOCS_DOMAIN}" mkdocs build --strict -f /app/docs/mkdocs.yml --site-dir /site

FROM nginx:1.27-alpine

COPY --from=build /site /usr/share/nginx/html

EXPOSE 80
