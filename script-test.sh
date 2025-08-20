#! /bin/bash

docker-compose -f docker-compose.test.yml run test_runner

sleep 1m

docker stop testing
docker rm testing

docker-compose down
