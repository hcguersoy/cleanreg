#!/bin/bash

source ../config/testutil.sh

oneTimeSetUp() {
   echo "Create images for registry and cleanreg"
   createRegistryImages
   createCleanregImage
   startRegistry
   echo "abc 2" > $CLEANREG_WORKSPACE/test.conf
}

oneTimeTearDown() {
  echo "Good bye"
  stopRegistry
}

test_n_and_f_cant_be_used_together() {  
   lastLine=$(runCleanregPython -f $CLEANREG_WORKSPACE/test.conf -n abc 2>&1 | tail -n 1 | tr -dC '[:print:]\t\n')
   echo $lastLine
   assertEquals "cleanreg.py: error: [-n] and [-f] cant be used together" "$lastLine"
}

test_k_has_to_be_positive() {  
   lastLine=$(runCleanreg -n abc -k -1 2>&1 | tail -n 1 | tr -dC '[:print:]\t\n')
   echo $lastLine
   assertEquals "cleanreg.py: error: [-k] has to be a positive integer!" "$lastLine"
}

test_n_and_k_works() {  
   lastLine=$(runCleanreg -n abc -k 1 2>&1 | tail -n 1 | tr -dC '[:print:]\t\n')
   echo $lastLine
   assertEquals "Aborted by user or nothing to delete." "$lastLine"
}

test_n_doesnt_work_without_k() {  
   lastLine=$(runCleanreg -n abc 2>&1 | tail -n 1 | tr -dC '[:print:]\t\n')
   echo $lastLine
   assertEquals "cleanreg.py: error: [-n] or [-cf] have to be used together with [-k]." "$lastLine"
}

test_cf_doesnt_work_without_k() {  
   lastLine=$(runCleanreg -cf 2>&1 | tail -n 1 | tr -dC '[:print:]\t\n')
   echo $lastLine
   assertEquals "cleanreg.py: error: [-n] or [-cf] have to be used together with [-k]." "$lastLine"
}

test_k_doesnt_work_without_cf_or_n() {  
   lastLine=$(runCleanreg -k 2 2>&1 | tail -n 1 | tr -dC '[:print:]\t\n')
   echo $lastLine
   assertEquals "cleanreg.py: error: [-n] or [-cf] have to be used together with [-k]." "$lastLine"
}

test_n_and_f_cant_be_used_together() {  
   lastLine=$(runCleanregPython -n abc -f $CLEANREG_WORKSPACE/test.conf 2>&1 | tail -n 1 | tr -dC '[:print:]\t\n')
   echo $lastLine
   assertEquals "cleanreg.py: error: [-n] and [-f] cant be used together" "$lastLine"
}

test_cf_and_f_can_be_used_together() {  
   lastLine=$(runCleanregPython -cf -k 2 -f $CLEANREG_WORKSPACE/test.conf 2>&1 | tail -n 1 | tr -dC '[:print:]\t\n')
   echo $lastLine
   assertEquals "Aborted by user or nothing to delete." "$lastLine"
}

test_f_works() {  
   lastLine=$(runCleanregPython -f $CLEANREG_WORKSPACE/test.conf 2>&1 | tail -n 1 | tr -dC '[:print:]\t\n')
   echo $lastLine
   assertEquals "Aborted by user or nothing to delete." "$lastLine"
}

test_either_f_n_or_cf_has_to_be_used() {  
   lastLine=$(runCleanreg 2>&1 | tail -n 1 | tr -dC '[:print:]\t\n')
   echo $lastLine
   assertEquals "cleanreg.py: error: [-n|-k] or [-cf|-k] or [-f] has to be used!" "$lastLine"
}

# load shunit2
. ../config/shunit2
