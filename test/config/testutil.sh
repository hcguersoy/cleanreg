#!/bin/bash

#Read directoryname of this script
DIRNAME=$(realpath $(dirname $(echo "${BASH_SOURCE[@]}[0]" | awk '{print $1;}')))
DOCKERFILEPATH="$DIRNAME/docker-registry"
#REGISTRYDATA="$DIRNAME/registrydata"

#######################################
# Creates an image for the cleanreg script.
# Globals:
#   None
# Arguments:
#   None 
#######################################
function createCleanregImage {
   docker build -t cleanreg $(realpath $DIRNAME/../..)
}

#######################################
# Runs cleanreg on localhost:5000
# Globals:
#   None
# Arguments:
#   Arguments will be passed to cleanreg
function runCleanreg {
   docker run --rm -it --net=host -v $(pwd):/data:ro cleanreg --quiet -r http://localhost:5000 --verbose $@
}

#######################################
# Creates images containing different configurated docker registries.
# Globals:
#   REGISTRYTAG The global env variable REGISTRYTAG defines the base version of the registries.
#               The version is the tag of the official registry-repository on Docker Hub.
#               If REGISTRYTAG is empty, the latest-tag is used
# Arguments:
#   None
# Results:
#   Generated image 'registry-default' is a standard registry with manifest-delete enabled
#   Generated image 'registry-basicauth' is based on 'registry-default' with basic auth enabled.
#   See docker-registry/Dockerfile-basicauth for basic auth credentials  
#######################################
function createRegistryImages {
   REGTAG=$REGISTRYTAG
   if [[ -z $REGTAG ]]; then
      REGTAG="latest"
   fi

   echo "Using Docker Registry in version $REGTAG. You can define the version by setting the REGISTRYTAG env variable"

   docker build -t registry-default   --build-arg TAG=$REGTAG -f $DOCKERFILEPATH/Dockerfile-default $DOCKERFILEPATH
   docker build -t registry-basicauth --build-arg BASEIMAGE=registry-default -f $DOCKERFILEPATH/Dockerfile-basicauth $DOCKERFILEPATH

}

#######################################
# Starts a registry as docker container.
# Globals:
#   None
# Arguments:
#   Imagename: The docker imagename to start a registry container.
#              If not set, 'registry-default' is used. See also function createRegistryImages 
#######################################
function startRegistry {
   IMAGENAME=$1
   if [[ -z $IMAGENAME ]]; then
      IMAGENAME="registry-default"
   fi

   docker rm -f registry
   echo "Starting registry based on image $IMAGENAME"
   #echo "Registrydata is stored in $REGISTRYDATA"
   #docker run -d --name registry -p 5000:5000 -v $REGISTRYDATA:/var/lib/registry $IMAGENAME
   docker run -d --name registry -p 5000:5000 $IMAGENAME
}

#######################################
# Creates a registry with basic auth enabled. See also function createRegistryImages
# Globals:
#   None
# Arguments:
#   None
#######################################
function startRegistryBasicAuth {
   startRegistry "registry-basicauth"
   docker login -u test -p secret http://localhost:5000
}


#######################################
# Runs the garbage collection on the currently running registry
# Globals:
#   None
# Arguments:
#   None
#######################################
function runGarbageCollection {
   docker exec -it registry bin/registry garbage-collect /etc/docker/registry/config.yml
}

#######################################
# Creates some test image-tags and pushes them into the local registry.
# It creates tags from TAGBEGIN to TAGEND for the image IMAGENAME.
# Globals:
#   None
# Arguments:
#   IMAGENAME (String, required) The image name used for the tags
#   TAGBEGIN (Integer)           A begin index for creating tags
#   TAGEND (Integer)             An ending index for creating tags
#######################################
function createTestdata {
   
   IMAGENAME=$1
   TAGBEGIN=$2
   TAGEND=$3

   if [[ -z $IMAGENAME ]]; then
      echo "no target image name as first parameter of $0"
      exit 1
   fi
   
   if [[ -z $TAGBEGIN ]]; then
      TAGBEGIN=1
   fi

   if [[ -z $TAGEND ]]; then
      TAGEND=5
   fi

   echo "Creating tags from $TAGBEGIN to $TAGEND for image localhost:5000/$IMAGENAME"

   # tag it multiple times...
   for i in `seq ${TAGBEGIN} ${TAGEND}`
   do
      echo "Creating image with tag ${i}"
      docker build --quiet --rm -t localhost:5000/${IMAGENAME}:${i} --build-arg tag=${i} --no-cache=true ${DIRNAME}/dummybox
      docker push localhost:5000/${IMAGENAME}:${i}
      # remove local copy
      docker rmi -f localhost:5000/${IMAGENAME}:${i}
   done
}

#######################################
# Pulls an image from the registry on localhost and return 0 for succes.
# Globals:
#   None
# Arguments:
#   IMAGENAME (required) Name of the image to pull from localhost:5000
#   TAG (required)       Tag of the image to pull from localhost:5000
# Returns:
#   0 if the image exists in the registry
#   or else another status code > 0  
#######################################
function pullImageFromLocalhost {
   IMAGENAME=$1
   TAG=$2

   if [[ -z $IMAGENAME ]]; then
      echo "no target image name as first parameter of $0"
      exit 1
   fi

   if [[ -z $IMAGENAME ]]; then
      echo "no tag specified as second parameter of $0"
      exit 1
   fi
   
   docker rmi -f localhost:5000/$IMAGENAME:$TAG
   docker pull localhost:5000/$IMAGENAME:$TAG
   EXITCODE=$?
   return $EXITCODE
}

#######################################
# Runs a shunit assert to verify that an image exists on the localhost:5000 registry
# Globals:
#   None
# Arguments:
#   IMAGENAME (required) Name of the image to pull from localhost:5000
#   TAG (required)       Tag of the image to pull from localhost:5000
#######################################
function assertImageExists {
    pullImageFromLocalhost $1 $2
    assertEquals 0 $EXITCODE
}

#######################################
# Runs a shunit assert to verify that an image does NOT exist on the localhost:5000 registry
# Globals:
#   None
# Arguments:
#   IMAGENAME (required) Name of the image to pull from localhost:5000
#   TAG (required)       Tag of the image to pull from localhost:5000
#######################################
function assertImageNotExists {
    pullImageFromLocalhost $1 $2
    assertNotEquals 0 $EXITCODE
}