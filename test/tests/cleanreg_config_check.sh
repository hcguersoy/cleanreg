#!/bin/bash

source ../config/testutil.sh

oneTimeSetUp() {
   echo "Create images for registry and cleanreg"
   createRegistryImages
   createCleanregImage
   startRegistry
   tee $CLEANREG_WORKSPACE/test.conf <<EOF > /dev/null
abc:
    keepimages: 2
    date: `date +%Y%m%d`
EOF
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

test_d_has_to_be_valid() {
   lastLine=$(runCleanreg -n abc -d 01012000 2>&1 | tail -n 1 | tr -dC '[:print:]\t\n')
   echo $lastLine
   assertEquals "cleanreg.py: error: [-d] format should be YYYYMMDD or YYYY-MM-DD" "$lastLine"
}

test_n_and_k_works() {
   lastLine=$(runCleanreg -n abc -k 1 2>&1 | tail -n 1 | tr -dC '[:print:]\t\n')
   echo $lastLine
   assertEquals "Aborted by user or nothing to delete." "$lastLine"
}

test_n_and_re_works() {
   lastLine=$(runCleanreg -n abc:1 -re 2>&1 | tail -n 1 | tr -dC '[:print:]\t\n')
   echo $lastLine
   assertEquals "Aborted by user or nothing to delete." "$lastLine"
}

test_n_and_d_works() {
   lastLine=$(runCleanreg -n abc -d 2000-01-01 2>&1 | tail -n 1 | tr -dC '[:print:]\t\n')
   echo $lastLine
   assertEquals "Aborted by user or nothing to delete." "$lastLine"
}

test_n_doesnt_work_without_k_re_or_d() {
   lastLine=$(runCleanreg -n abc 2>&1 | tail -n 1 | tr -dC '[:print:]\t\n')
   echo $lastLine
   assertEquals "cleanreg.py: error: [-n] or [-cf] have to be used together with [-k], [-re] or [-d]." "$lastLine"
}

test_cf_doesnt_work_without_k_re_or_d() {
   lastLine=$(runCleanreg -cf 2>&1 | tail -n 1 | tr -dC '[:print:]\t\n')
   echo $lastLine
   assertEquals "cleanreg.py: error: [-n] or [-cf] have to be used together with [-k], [-re] or [-d]." "$lastLine"
}

test_k_doesnt_work_without_cf_or_n() {
   lastLine=$(runCleanreg -k 2 2>&1 | tail -n 1 | tr -dC '[:print:]\t\n')
   echo $lastLine
   assertEquals "cleanreg.py: error: [-n] or [-cf] have to be used together with [-k], [-re] or [-d]." "$lastLine"
}

test_re_doesnt_work_without_cf_or_n() {
   lastLine=$(runCleanreg -re 2>&1 | tail -n 1 | tr -dC '[:print:]\t\n')
   echo $lastLine
   assertEquals "cleanreg.py: error: [-n] or [-cf] have to be used together with [-k], [-re] or [-d]." "$lastLine"
}

test_d_doesnt_work_without_cf_or_n() {
   lastLine=$(runCleanreg -d 2000-01-01 2>&1 | tail -n 1 | tr -dC '[:print:]\t\n')
   echo $lastLine
   assertEquals "cleanreg.py: error: [-n] or [-cf] have to be used together with [-k], [-re] or [-d]." "$lastLine"
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

test_f_with_k_works() {
   createTestdata "abc" 1 5
   assertImageExists "abc" 1
   assertImageExists "abc" 2
   assertImageExists "abc" 3
   assertImageExists "abc" 4
   assertImageExists "abc" 5

   tee $CLEANREG_WORKSPACE/test.conf <<EOF > /dev/null
abc:
    keepimages: 2
EOF
   runCleanregPython -f $CLEANREG_WORKSPACE/test.conf
   assertImageNotExists "abc" 1
   assertImageNotExists "abc" 2
   assertImageNotExists "abc" 3
   assertImageExists "abc" 4
   assertImageExists "abc" 5
}

test_f_with_regex_works() {
   createTestdata "abc" 1 5
   assertImageExists "abc" 1
   assertImageExists "abc" 2
   assertImageExists "abc" 3
   assertImageExists "abc" 4
   assertImageExists "abc" 5

   tee $CLEANREG_WORKSPACE/test.conf <<EOF > /dev/null
abc:
    tag: 1|2
EOF
   runCleanregPython -f $CLEANREG_WORKSPACE/test.conf -re
   assertImageNotExists "abc" 1
   assertImageNotExists "abc" 2
   assertImageExists "abc" 3
   assertImageExists "abc" 4
   assertImageExists "abc" 5
}

test_f_with_date_works() {
   createTestdata "abc" 1 5
   assertImageExists "abc" 1
   assertImageExists "abc" 2
   assertImageExists "abc" 3
   assertImageExists "abc" 4
   assertImageExists "abc" 5

   tee $CLEANREG_WORKSPACE/test.conf <<EOF > /dev/null
abc:
    date: `date +%Y%m%d`
EOF
   runCleanregPython -f $CLEANREG_WORKSPACE/test.conf
   assertImageExists "abc" 1
   assertImageExists "abc" 2
   assertImageExists "abc" 3
   assertImageExists "abc" 4
   assertImageExists "abc" 5
}

# load shunit2
. ../config/shunit2
