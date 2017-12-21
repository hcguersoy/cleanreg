#!/bin/bash
set -e

#######################################
#Runs a testfile within the testrunner container
#Arguments:
#  FILENAME the name of the testfile script inside the test/tests directory
#  REGISTRYTAG tag of the registry being used
#######################################
function runTestFile {
   docker run --rm -it -e REGISTRYTAG=$2 --net=host -v $(pwd):/workspace -e CLEANREG_WORKSPACE=/workspace -v /var/run/docker.sock:/var/run/docker.sock:ro testrunner "cd /workspace/test/tests; ls -la; ./$1"
   EXITCODE=$?
   if [[ $EXITCODE -ne 0 ]]; then
      echo "Test failure"
      exit 1
   fi
}

#Create the testrunner image
docker build -t testrunner -f ./config/Dockerfile.testrunner ./config
chmod -R +x ./tests
cd ..

#Run the testfiles
runTestFile simple_clean.sh 2.5.1
sleep 5
runTestFile simple_clean.sh 2.6.1
sleep 5
runTestFile simple_clean.sh latest

sleep 5
runTestFile clean_full_catalog.sh 2.6.1

sleep 5
runTestFile cleanreg_config_check.sh 2.6.1
