#!/bin/bash

REGISTRYDATA="/C/Users/krummenauer/workspaceCleanReg/cleanreg/registry-data"
DIRNAME=$(dirname $(echo "${BASH_SOURCE[@]}[0]" | awk '{print $1;}'))
DOCKERFILEPATH=$(realpath $DIRNAME/docker-registry)


function startRegistryBasicAuth {
   docker rm -f registry
   echo $DOCKERFILEPATH
   docker build -t registry-basicauth -f $DOCKERFILEPATH/Dockerfile-basicauth $DOCKERFILEPATH
   docker run -d --name registry -p 5000:5000 -v $REGISTRYDATA:/var/lib/registry registry-basicauth
}

function startRegistry {
   docker rm -f registry
   docker run -d --name registry -p 5000:5000 -v $REGISTRYDATA:/var/lib/registry registry:2.6.1
}
