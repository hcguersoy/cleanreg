#!/bin/bash

source ../config/testutil.sh


setUp() {
   echo "Create images for registry and cleanreg"
   createRegistryImages
   createCleanregImage
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
   runCleanreg -n abc -k 2
   assertImageNotExists "abc" 1
   assertImageNotExists "abc" 2
   assertImageNotExists "abc" 3
   assertImageExists "abc" 4
   assertImageExists "abc" 5
    
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
   runCleanreg -n abc -k 2
   assertImageExists "abc" 1
   assertImageExists "abc" 2
   assertImageExists "abc" 3
   assertImageExists "abc" 4
   assertImageExists "abc" 5

   #cleanreg with credentials should delete imagetags
   runCleanreg -n abc -k 2 -u test -pw secret

   assertImageNotExists "abc" 1
   assertImageNotExists "abc" 2
   assertImageNotExists "abc" 3
   assertImageExists "abc" 4
   assertImageExists "abc" 5

}

# load shunit2
. ../config/shunit2
