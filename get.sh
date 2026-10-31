#!/bin/bash

if [ -z "$SKODA_PERIOD" ];
then
  sleepPeriod=3600
else
  sleepPeriod=$SKODA_PERIOD
fi

while :
do
  date
  echo "### Start Get Skoda Data ###"
  python3 getskodadata.py
  RET=$?
  if [ ${RET} -ne 0 ];
  then
    echo "Exit status not 0, retry in 1 min"
    sleep 60
    python3 getskodadata.py
  fi
  date
  echo "### Sleep $sleepPeriod s"
  sleep $sleepPeriod
done
