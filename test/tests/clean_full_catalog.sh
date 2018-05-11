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
   createTestdata "alpine" 1 4
   createTestdata "mysql" 1 5
   createTestdata "mongo" 1 2
   createTestdata "postgres" 1 3
   createTestdata "redis" 1 3

   assertImageExists "consul" 1
   assertImageExists "consul" 2
   assertImageExists "consul" 3
   
   assertImageExists "elasticsearch" 1
   assertImageExists "elasticsearch" 2
   assertImageExists "elasticsearch" 3
   
   assertImageExists "alpine" 1
   assertImageExists "alpine" 2
   assertImageExists "alpine" 3
   assertImageExists "alpine" 4

   assertImageExists "mysql" 1
   assertImageExists "mysql" 2
   assertImageExists "mysql" 3
   assertImageExists "mysql" 4
   assertImageExists "mysql" 5

   assertImageExists "mongo" 1
   assertImageExists "mongo" 2

   assertImageExists "postgres" 1
   assertImageExists "postgres" 2
   assertImageExists "postgres" 3

   assertImageExists "redis" 1
   assertImageExists "redis" 2
   assertImageExists "redis" 3

   # setup conf file
   tee $CLEANREG_WORKSPACE/test.conf <<EOF > /dev/null
consul 20 _ _
elasticsearch 1 _ _
dummybox 10 _ _
mongo 1 _ _
postgres 0 _ `date +%d.%m.%Y`
redis 0 2 _
EOF

   # run cleanreg with --clean-full-catalog -k 2
   # keeping 2 images of alpine and mysql, because they are not in the test.conf
   runCleanregPython -f $CLEANREG_WORKSPACE/test.conf -vvv --clean-full-catalog -k 2 -re 2 -d `date +%d.%m.`$((`date +%Y`+1))
   
   assertImageExists "consul" 1
   assertImageExists "consul" 2
   assertImageExists "consul" 3
   
   assertImageNotExists "elasticsearch" 1
   assertImageNotExists "elasticsearch" 2
   assertImageExists "elasticsearch" 3
   
   assertImageNotExists "alpine" 1
   assertImageExists "alpine" 2
   assertImageExists "alpine" 3
   assertImageExists "alpine" 4

   assertImageNotExists "mysql" 1
   assertImageExists "mysql" 2
   assertImageNotExists "mysql" 3
   assertImageExists "mysql" 4
   assertImageExists "mysql" 5

   assertImageNotExists "mongo" 1
   assertImageExists "mongo" 2

   assertImageExists "postgres" 1
   assertImageExists "postgres" 2
   assertImageExists "postgres" 3

   assertImageNotExists "redis" 1
   assertImageExists "redis" 2
   assertImageNotExists "redis" 3

}


# load shunit2
. ../config/shunit2
