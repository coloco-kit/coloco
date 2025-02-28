# Dev Container

FROM python:3.12-alpine

RUN apk add --update nodejs npm

# Python Install
WORKDIR /app
ADD ./requirements.txt /app/requirements.txt
RUN python -m pip install -r /app/requirements.txt

# TODO: remove this when fakit is a package
ADD ./fakit/requirements.txt /app/fakit/requirements.txt
RUN python -m pip install -r /app/fakit/requirements.txt

# Node Install
RUN mkdir /.npm && chown -R 1000:1000 "/.npm"
ADD ./+node/package.json /app/package.json
ADD ./+node/package-lock.json /app/package-lock.json
RUN npm install

# Codegen
RUN npm install -g @hey-api/client-fetch @hey-api/openapi-ts

ADD . /app

# ADD backend /api
# RUN python -c "from main import app; from fakit.codegen import generate_openapi_schema; generate_openapi_schema(app.api, '/tmp/openapi.json')"

# # Frontend Build

# FROM node:20-alpine as frontend

# WORKDIR /app

# ADD frontend/package.json /app/package.json
# ADD frontend/package-lock.json /app/package-lock.json

# RUN npm install

# COPY --from=backend /tmp/openapi.json /tmp/openapi.json

# RUN npx @hey-api/openapi-ts \
#     --base https://mysite.app \
#     --input /tmp/openapi.json \
#     --output /app/src/backend \
#     --client legacy/fetch

# ADD frontend /app
# RUN npm run build

# # Combined Image

# FROM backend

# COPY --from=frontend /app/dist /api/static
# ENV MODE=production

CMD ["python", "-m", "fakit", "start"]
# CMD ["uvicorn", "main:api.service", "--host", "0.0.0.0", "--port", "80"]