#!/bin/bash
# docker entrypoint timed loop with retry

# v01 2026-11-01 created standard script

# varables
sleepMins=10
retryMins=20

# calculations
sleepSecs=$( bc <<< "$sleepMins * 60" )
retrySecs=$( bc <<< "$sleepSecs * 60" )

# main loop
while :
do
  timeStamp=$( date )
  timeStart=$( date +%s )
  echo " TRIGGER : ${timeStamp}"

  python3 skoda2influxdb.py

  timeStop=$( date +%s )
  timeSecs=$( bc <<< "$timeStop - $timeStart" )
  timeMins=$( bc <<< "$timeSecs / 60" )
  pollRate=$( bc <<< "60 / ( $sleepMins + $timeMins )" )

  printf " RUNTIME : %.1f mins [ %i secs ]\n" ${timeMins} ${timeSecs}
  printf "    RATE : %.1f API calls per hour\n" ${pollRate}

  returnStatus=$?
  if [ ${returnStatus} -ne 0 ]; then
    echo "   ERROR : ${returnStatus}"
    echo "   RETRY : ${retryMins} mins..."
  else
    echo "    WAIT : ${sleepMins} mins..."
    sleep $sleepSecs
  fi
done
