docker build -t opal-client:local -f docker/Dockerfile --target client .
docker build -t opal-server:local -f docker/Dockerfile --target server . 

docker compose -f docker/docker-compose-alpine-test.yml up