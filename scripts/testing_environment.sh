#!/usr/bin/env bash

#needs to be run from the root directory

docker build -f scripts/Dockerfile --no-cache -t qtrvsim-test .

docker run -d --rm \
	--name qtrvsim-eval-test \
	--privileged \
	-v /sys/fs/cgroup:/sys/fs/cgroup:rw \
	--cgroupns=host \
	-p 8108:8000 \
	-p 8100:80 \
	-p 8104:443 \
	qtrvsim-test

docker exec -it qtrvsim-eval-test /bin/bash