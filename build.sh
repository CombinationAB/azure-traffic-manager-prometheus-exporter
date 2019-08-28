#!/bin/bash

IMAGE_NAME=combination/azure-traffic-manager-prometheus-exporter
IMAGE_VERSION=0.0.3

docker build -t $IMAGE_NAME -t $IMAGE_NAME:$IMAGE_VERSION $(dirname $0)

