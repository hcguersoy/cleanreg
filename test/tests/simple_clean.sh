#!/bin/bash
setopt shwordsplit

source ../config/testutil.sh

setUp() {
   echo "Create images for registry and cleanreg"
   createRegistryImages
   createCleanregImage
}

# is ignored...
teardown() {
  stopRegistry
}

oneTimeTearDown() {
  echo " **** Good bye **** "
  stopRegistry
}

testCleanASingleRepo() {
   startRegistry

   #setup testdata
   createTestdata "abc" 1 5
   assertImageExists "abc" 1
   assertImageExists "abc" 2
   assertImageExists "abc" 3
   assertImageExists "abc" 4
   assertImageExists "abc" 5

   #run cleanreg
   runCleanreg -n abc -k 2 -i
   assertImageNotExists "abc" 1
   assertImageNotExists "abc" 2
   assertImageNotExists "abc" 3
   assertImageExists "abc" 4
   assertImageExists "abc" 5
}

testCleanASingleRepoKeepImages() {
   startRegistry

   #setup testdata
   createIdenticalTestdata "abc" 1 5
   assertImageExists "abc" 1
   assertImageExists "abc" 2
   assertImageExists "abc" 3
   assertImageExists "abc" 4
   assertImageExists "abc" 5

   #run cleanreg
   runCleanreg -n abc -k 2 -i
   assertImageExists "abc" 1
   assertImageExists "abc" 2
   assertImageExists "abc" 3
   assertImageExists "abc" 4
   assertImageExists "abc" 5
}

testCleanASingleRepoRegex() {
   startRegistry

   #setup testdata
   createTestdata "abc" 1 5
   assertImageExists "abc" 1
   assertImageExists "abc" 2
   assertImageExists "abc" 3
   assertImageExists "abc" 4
   assertImageExists "abc" 5

   #cleanreg with a regex matching abc:1 and abc:2 will delete those
   runCleanreg -n abc:1\|2 -re -i
   assertImageNotExists "abc" 1
   assertImageNotExists "abc" 2
   assertImageExists "abc" 3
   assertImageExists "abc" 4
   assertImageExists "abc" 5

   #regex is not enabled so the tagname won't match any
   runCleanreg -n abc:3\|4 -i
   assertImageNotExists "abc" 1
   assertImageNotExists "abc" 2
   assertImageExists "abc" 3
   assertImageExists "abc" 4
   assertImageExists "abc" 5
}

testCleanASingleRepoDate() {
   startRegistry

   #setup testdata
   createTestdata "abc" 1 5
   assertImageExists "abc" 1
   assertImageExists "abc" 2
   assertImageExists "abc" 3
   assertImageExists "abc" 4
   assertImageExists "abc" 5

   #cleanreg with todays date sholdn't delete any images
   runCleanreg -n abc -s $(($(date +%Y)-1))$(date '+%m%d') -i
   assertImageExists "abc" 1
   assertImageExists "abc" 2
   assertImageExists "abc" 3
   assertImageExists "abc" 4
   assertImageExists "abc" 5

   #same test with different date format
   runCleanreg -n abc -s $(($(date +%Y)-1))$(date '+-%m-%d') -i
   assertImageExists "abc" 1
   assertImageExists "abc" 2
   assertImageExists "abc" 3
   assertImageExists "abc" 4
   assertImageExists "abc" 5

   #same test with different date format
   runCleanreg -n abc -s $(($(date +%Y)-1))$(date '+%m%dT000000') -i
   assertImageExists "abc" 1
   assertImageExists "abc" 2
   assertImageExists "abc" 3
   assertImageExists "abc" 4
   assertImageExists "abc" 5

   #same test with different date format
   runCleanreg -n abc -s $(($(date +%Y)-1))$(date '+-%m-%dT00:00:00') -i
   assertImageExists "abc" 1
   assertImageExists "abc" 2
   assertImageExists "abc" 3
   assertImageExists "abc" 4
   assertImageExists "abc" 5

   #cleanreg with a date in the future should delete all images
   runCleanreg -n abc -s $(($(date +%Y)+1))$(date +%m%d) -i
   assertImageNotExists "abc" 1
   assertImageNotExists "abc" 2
   assertImageNotExists "abc" 3
   assertImageNotExists "abc" 4
   assertImageNotExists "abc" 5
}

testCleanASingleRepoRemoveAllImagesWithOneDigest() {
   startRegistry

   #setup testdata
   createIdenticalTestdata "abc" 1 5
   assertImageExists "abc" 1
   assertImageExists "abc" 2
   assertImageExists "abc" 3
   assertImageExists "abc" 4
   assertImageExists "abc" 5

   #run cleanreg WITHOUT -i (ignore) flag
   runCleanreg -n abc -k 4
   assertImageNotExists "abc" 1
   assertImageNotExists "abc" 2
   assertImageNotExists "abc" 3
   assertImageNotExists "abc" 4
   assertImageNotExists "abc" 5
}

testCleanASingleRepoWithBasicAuthRegistry() {
   startRegistryBasicAuth

   #setup testdata
   createTestdata "abc" 1 5
   assertImageExists "abc" 1
   assertImageExists "abc" 2
   assertImageExists "abc" 3
   assertImageExists "abc" 4
   assertImageExists "abc" 5

   #Cleanreg without credentials -> no changes
   runCleanreg -n abc -k 2 -i
   assertImageExists "abc" 1
   assertImageExists "abc" 2
   assertImageExists "abc" 3
   assertImageExists "abc" 4
   assertImageExists "abc" 5

   #cleanreg with credentials should delete imagetags
   runCleanreg -n abc -k 2 -u test -pw secret -i

   assertImageNotExists "abc" 1
   assertImageNotExists "abc" 2
   assertImageNotExists "abc" 3
   assertImageExists "abc" 4
   assertImageExists "abc" 5
}

# load shunit2
. ../config/shunit2
