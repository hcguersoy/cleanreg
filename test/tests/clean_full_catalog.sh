#!/bin/bash
setopt shwordsplit

source ../config/testutil.sh

setUp() {
   echo "Create images for registry and cleanreg"
   createRegistryImages
   createCleanregImage
}

teardown() {
  stopRegistry
}

oneTimeTearDown() {
  echo " **** Good bye **** "
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

   echo " *** Created test images, checking if they are in the registry"

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

    echo " *** creating configuration file"

   # setup conf file
   tee $CLEANREG_WORKSPACE/test.conf <<EOF > /dev/null
consul:
    keepimages: 20
elasticsearch:
    keepimages: 1
dummybox:
    keepimages: 10
mongo:
    keepimages: 1
postgres:
    keepimages: 0
    keepsince: `date +%Y%m%d`
redis:
    tag: 2
    keepimages: 0
EOF

    echo " *** running cleanreg"

   # run cleanreg with --clean-full-catalog -k 2
   # keeping 2 images of alpine and mysql, because they are not in the test.conf
   runCleanregPython -f $CLEANREG_WORKSPACE/test.conf -vvv --clean-full-catalog -k 2 -re -s $((`date +%Y`+1))`date +%m%d`

    echo " *** checks after cleanreg"
   assertImageExists "consul" 1
   assertImageExists "consul" 2
   assertImageExists "consul" 3

   assertImageNotExists "elasticsearch" 1
   assertImageNotExists "elasticsearch" 2
   assertImageExists "elasticsearch" 3

   assertImageNotExists "alpine" 1
   assertImageNotExists "alpine" 2
   assertImageExists "alpine" 3
   assertImageExists "alpine" 4

   assertImageNotExists "mysql" 1
   assertImageNotExists "mysql" 2
   assertImageNotExists "mysql" 3
   assertImageExists "mysql" 4
   assertImageExists "mysql" 5

   assertImageNotExists "mongo" 1
   assertImageExists "mongo" 2

   assertImageExists "postgres" 1
   assertImageExists "postgres" 2
   assertImageExists "postgres" 3

   assertImageExists "redis" 1
   assertImageNotExists "redis" 2
   assertImageExists "redis" 3

}


# load shunit2
. ../config/shunit2
