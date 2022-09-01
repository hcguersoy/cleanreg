#!/bin/bash

#######################################
#Runs a testfile within the testrunner container
#Arguments:
#  FILENAME the name of the testfile script inside the test/tests directory
#  REGISTRYTAG tag of the registry being used
#######################################
function runTestFile {
   echo "Running testfile ${1} with registry version ${2}"
   docker run --rm -e REGISTRYTAG="$2" --net=host -v $(pwd):/workspace -e CLEANREG_WORKSPACE=/workspace -v /var/run/docker.sock:/var/run/docker.sock:ro testrunner "cd /workspace/test/tests; ls -la; ./$1"
   EXITCODE=$?
   if [[ $EXITCODE -ne 0 ]]; then
      echo "Test failure"
      exit 1
   fi
}

#Create the testrunner image
docker build -t testrunner -f ./config/Dockerfile.testrunner ./config
echo "Finished building testrunner"

chmod -R +x ./tests
cd ..

#Run the testfiles
sleep 5
echo "Starting tests"

sleep 5
runTestFile simple_clean.sh 2.8.1

sleep 5
runTestFile clean_full_catalog.sh 2.8.1

sleep 5
runTestFile cleanreg_config_check.sh 2.8.1
