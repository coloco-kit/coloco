# Backend Build

FROM python:3.12-alpine as backend

WORKDIR /api

ADD backend/requirements.txt /api/requirements.txt
RUN python -m pip install -r /api/requirements.txt

ADD backend /api
RUN python -c "from main import api; from service import generate_openapi_schema; generate_openapi_schema(api, '/tmp/openapi.json')"

# Frontend Build

FROM node:20-alpine as frontend

WORKDIR /app

ADD frontend/package.json /app/package.json
ADD frontend/package-lock.json /app/package-lock.json

RUN npm install

COPY --from=backend /tmp/openapi.json /tmp/openapi.json

RUN npx @hey-api/openapi-ts \
    --base https://mysite.app \
    --input /tmp/openapi.json \
    --output /app/src/backend \
    --client legacy/fetch

ADD frontend /app
RUN npm run build

# Combined Image

FROM backend

COPY --from=frontend /app/dist /api/static
ENV MODE=production

CMD ["uvicorn", "main:api.service", "--host", "0.0.0.0", "--port", "80"]