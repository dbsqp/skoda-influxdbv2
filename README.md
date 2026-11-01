Docker image to get Skoda car status via API and push results into an InfluxDB bucket.

*UNDER DEVELOPEMENT - NOT STABLE*

## InfluxDBv2 Setup

Setup InfluxDBv2, create bucket and create a token with write permissions for bucket.

## Docker Setup
https://hub.docker.com/repository/docker/dbsqp/skoda-influxdbv2
```
$ docker run -d \
 -e SKODA_VIN="<Skoda VIN>" \
 -e INFLUXDB2_HOST="<influxDBv2 SERVER>" \
 -e INFLUXDB2_PORT="8086" \
 -e INFLUXDB2_ORG="Home" \
 -e INFLUXDB2_TOKEN="" \
 -e INFLUXDB2_BUCKET="DEV-Skoda" \
 --name "InfluxDB-Skoda" \
dbsqp/skoda-influxdbv2:latest
```

# Options
```
 -e SKODA_KEY="<Skoda API Key>" \
 ```
Prefered method is via docker volume of file at /apikey to allow easy manual update of expired key via mySkoda app. Note API does not use oauth.
```
 -e INFLUXDB2_SSL="True" \
 -e INFLUXDB2_SSL_VERIFY="False" \
```

# Debug
```
 -e DEBUG="true"
```
Report out further details in log.
