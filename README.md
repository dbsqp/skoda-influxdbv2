Docker image to get Skoda car date via API and push results into an influxdb bucket.

UNDER DEVELOPEMENT

## InfluxDBv2 Setup

Setup InfluxDBv2, create bucket and create a token with write permissions for said bucket.

## Docker Setup
https://hub.docker.com/repository/docker/dbsqp/skoda-influxdbv2
```
$ docker run -d \
 -e SKODA_VIN="<Skoda VIN>" \
 -e SKODA_KEY="<Skoda API Key>" \
 -e INFLUXDB2_HOST="<influxDBv2 SERVER>" \
 -e INFLUXDB2_PORT="8086" \
 -e INFLUXDB2_ORG="Home" \
 -e INFLUXDB2_TOKEN="" \
 -e INFLUXDB2_BUCKET="DEV-Skoda" \
 --name "Influx-Skoda" \
dbsqp/skoda-influxdbv2:latest
```
# Options
SKODA_KEY is optional override. Prefered method is to take from file volume to allow easy update via mySkoda app upon expiry.
```
 -e INFLUXDB2_SSL="True" \
 -e INFLUXDB2_SSL_VERIFY="False" \
```


# Debug
To report out further details in the log enable debug:
```
 -e DEBUG="true"
```
