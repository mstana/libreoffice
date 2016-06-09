#!/bin/bash
sudo -u test behave -D package=$1 -k -f plain -f plain -o /tmp/report_$TEST.log; rc=$?
RESULT="FAIL"
if [ $rc -eq 0 ]; then
  RESULT="PASS"
fi

rhts-report-result $TEST $RESULT "/tmp/report_$TEST.log"
exit $rc
