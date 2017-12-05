#!/bin/bash

source ../config/testutil.sh

setUp() {
   echo "Create images for registry and cleanreg"
   createRegistryImages
   createCleanregImage
}

teardown() {
  echo "Good bye"
  stopRegistry
}

test_CleanFullCatalog_uses_keepNumber_for_all_repos_if_not_specified_in_confFile() {
   startRegistry

   #setup testdata
   createTestdata "consul" 1 3
   createTestdata "elasticsearch" 1 3
   createTestdata "alpine" 1 3
   createTestdata "mysql" 1 4
   createTestdata "mongo" 1 2
   
   assertImageExists "consul" 1
   assertImageExists "consul" 2
   assertImageExists "consul" 3
   
   assertImageExists "elasticsearch" 1
   assertImageExists "elasticsearch" 2
   assertImageExists "elasticsearch" 3
   
   assertImageExists "alpine" 1
   assertImageExists "alpine" 2
   assertImageExists "alpine" 3
   
   assertImageExists "mysql" 1
   assertImageExists "mysql" 2
   assertImageExists "mysql" 3
   assertImageExists "mysql" 4

   assertImageExists "mongo" 1
   assertImageExists "mongo" 2

   # setup conf file
   tee test.conf <<EOF > /dev/null
consul 20
elasticsearch 1
dummybox 10 
mongo 1
EOF

   # run cleanreg with --clean-full-catalog -k 2
   # keeping 2 images of alpine and mysql, because they are not in the test.conf
   runCleanreg -f /data/test.conf -vvv --clean-full-catalog -k 2
   
   assertImageExists "consul" 1
   assertImageExists "consul" 2
   assertImageExists "consul" 3
   
   assertImageNotExists "elasticsearch" 1
   assertImageNotExists "elasticsearch" 2
   assertImageExists "elasticsearch" 3
   
   assertImageNotExists "alpine" 1
   assertImageExists "alpine" 2
   assertImageExists "alpine" 3
   
   assertImageNotExists "mysql" 1
   assertImageNotExists "mysql" 2
   assertImageExists "mysql" 3
   assertImageExists "mysql" 4

   assertImageNotExists "mongo" 1
   assertImageExists "mongo" 2

   rm test.conf
}


# load shunit2
. ../config/shunit2
