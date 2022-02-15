#!/bin/bash
# creates dummy image layers for testing purposes based on busybox
# useage: createdummydata.sh <registry-url> <amount layers>
# e.g.: createdummydata.sh localhost:5000 10

reg=$1
tags=$2

echo $1
echo $2

echo "Will create busybox ${tags} on server ${reg}."

# tag it multiple times...
for i in `seq 1 ${tags}`
do
  echo "Creating image with tag ${i}"
  docker build --rm -t ${reg}/dummybox:${i} --build-arg tag=${i} --no-cache=true -f test/config/dummybox/Dockerfile .
  docker push ${reg}/dummybox:${i}
  # remove local copy
  docker rmi -f ${reg}/dummybox:${i}
done
