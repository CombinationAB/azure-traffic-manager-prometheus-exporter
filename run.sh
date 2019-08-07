#!/bin/bash

. $(dirname $0)/build.sh

if [ ! -f "$1" ]; then
  echo "Usage: $0 {azurejson} {tm-name}" >> /dev/stderr
  exit 1
fi

docker run -e AZ_POLL_INTERVAL=1 -v $(readlink -f $1):/azure.json:ro $IMAGE_NAME:$IMAGE_VERSION $2


