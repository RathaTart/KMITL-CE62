#!/bin/bash

apt-get update -y
apt-get install -y docker.io curl

systemctl enable docker
systemctl start docker

docker rm -f wakapi || true

# Supply these values through the environment or cloud-init; never commit credentials.
docker run -d \
  --name wakapi \
  --restart unless-stopped \
  -p 3000:3000 \
  -e WAKAPI_PASSWORD_SALT="${WAKAPI_PASSWORD_SALT:?Set WAKAPI_PASSWORD_SALT}" \
  -e WAKAPI_DB_PORT=5432 \
  -e WAKAPI_LISTEN_IPV4=0.0.0.0 \
  -e WAKAPI_INSECURE_COOKIES=true \
  -e WAKAPI_DB_TYPE=postgres \
  -e WAKAPI_DB_USER="${WAKAPI_DB_USER:?Set WAKAPI_DB_USER}" \
  -e WAKAPI_DB_NAME="${WAKAPI_DB_NAME:?Set WAKAPI_DB_NAME}" \
  -e WAKAPI_DB_PASSWORD="${WAKAPI_DB_PASSWORD:?Set WAKAPI_DB_PASSWORD}" \
  -e WAKAPI_DB_HOST="${WAKAPI_DB_HOST:?Set WAKAPI_DB_HOST}" \
  -e WAKAPI_DB_SSL=true \
  ghcr.io/muety/wakapi:2.17.1
