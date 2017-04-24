#!/bin/bash

source ../config/testutil.sh


setUp(){
   startRegistryBasicAuth
}


testEquality()
{
  #docker pull busybox
  assertEquals 1 2
}

# load shunit2
. ../config/shunit-2.1/src/shunit2
