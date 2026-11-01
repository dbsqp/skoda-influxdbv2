#!/usr/bin/env python3
# encoding=utf-8

# get skoda data from API based on VIN and puch to InfluxDB

# local test setup
# python3 -c "help('modules')"
# pip3 install pytz influxdb_client requests


# setup python
from pytz import timezone
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS
import json
import os
import sys
import socket
import subprocess
import platform
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from os import path

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


# debug enviroment variables
debug_str=os.getenv("DEBUG", None)
if debug_str is not None:
	debug = debug_str.lower() == "true"
else:
	debug = False

host = os.getenv("HOST", socket.gethostname())


# influxDBv2 envionment variables
influxdb2_host=os.getenv('INFLUXDB2_HOST', "localhost")
influxdb2_port=int(os.getenv('INFLUXDB2_PORT', "8086"))
influxdb2_org=os.getenv('INFLUXDB2_ORG', "Home")
influxdb2_token=os.getenv('INFLUXDB2_TOKEN', "token")
influxdb2_bucket=os.getenv('INFLUXDB2_BUCKET', "DEV")

influxdb2_ssl_str=os.getenv('INFLUXDB2_SSL', "False")
if influxdb2_ssl_str is not None:
    influxdb2_ssl = influxdb2_ssl_str.lower() == "true"
else:
    influxdb2_ssl = False

influxdb2_ssl_verify_str=os.getenv('INFLUXDB2_SSL_VERIFY', "False")
if influxdb2_ssl_verify_str is not None:
    influxdb2_ssl_verify = influxdb2_ssl_verify_str.lower() == "true"
else:
    influxdb2_ssl_verify = False

# skoda api envionment variables
skodaapi_vin = os.getenv('SKODA_VIN',"UNKNOWN")
skodaapi_key = os.getenv('SKODA_KEY',"UNKNOWN")

# file key - override
keyFile = path.abspath(path.join(path.dirname(path.abspath(__file__)), "apikey"))

if os.path.exists(keyFile):
    FILE = open(keyFile, "r")
    skodaapi_key = FILE.read().rstrip()
    FILE.close()
    print("  apikey : "+skodaapi_key )

# hard encoded envionment varables for testing
if os.path.exists('private-skoda.py'):
    print("   local : private-skoda.py")
    exec(compile(source=open('private-skoda.py').read(), filename='private-skoda.py', mode='exec'))
    debug = True

# skoda api data test
if skodaapi_vin == "UNKNOWN" or skodaapi_key == "UNKNOWN":
    if skodaapi_vin == "UNKNOWN":
        print ( "SKODA_VIN : "+skodaapi_vin )
    if skodaapi_key == "UNKNOWN":
        print ( "SKODA_KEY : "+skodaapi_key )
    print("     exit : return status = 2" )
    sys.exit(2)


# report debug status
if debug:
	print ( "   debug : TRUE" )


# influxDBv2
if influxdb2_ssl_str:
    influxdb2_url="https://" + influxdb2_host + ":" + str(influxdb2_port)
else:
    influxdb2_url="http://" + influxdb2_host + ":" + str(influxdb2_port)
	
if influxdb2_ssl_verify:
	client = InfluxDBClient(url=influxdb2_url, token=influxdb2_token, org=influxdb2_org, verify_ssl=True)
else:
	client = InfluxDBClient(url=influxdb2_url, token=influxdb2_token, org=influxdb2_org, verify_ssl=False)

write_api = client.write_api(write_options=SYNCHRONOUS)

if debug:
    print ( "  influx : "+influxdb2_url )
    print ( "  bucket : "+influxdb2_bucket )
    if influxdb2_ssl_verify:
        print ( "  verify : TRUE" )
    else:
        print ( "  verify : FALSE" )

def write_influxdb():
    if debug:
        print ("\nInfluxDB : info = "+senddata["tags"]["info"]+" > "+influxdb2_bucket)
        print (json.dumps(senddata,indent=4))
    write_api.write(bucket=influxdb2_bucket, org=influxdb2_org, record=[senddata], write_precision="s")


# call API
dtNow = datetime.now()
epochNow = int( dtNow.timestamp() )

print( "call API : VIN = "+skodaapi_vin )

apiHEADR = { "X-API-Key" : skodaapi_key }
skodaURL = "https://public.api.connect.skoda-auto.cz/api/v1/vehicles/"+skodaapi_vin
#apiQUERY = {'include': ['status', 'odometer', 'fuelStatus', 'parkingPosition']}
apiQUERY = {}

if debug:
    print ( "     key : "+skodaapi_key )
    print ( "     url : "+skodaURL )
    #print ( "hdr: " )
    #[ print ( f"{key}: {value}") for key, value in apiHEADR.items() ]
    #print ( "qry: " )
   # [ print ( f"{key}: {value}") for key, value in apiQUERY.items() ]

responseFull = requests.get(skodaURL, params=apiQUERY, headers=apiHEADR)
responseStatus = responseFull.status_code
responseJSON = responseFull.json()
responseHeaders = responseFull.headers

headerLimit = responseHeaders['RateLimit-Limit']
headerRemaining = responseHeaders['RateLimit-Remaining']
headerReset = responseHeaders['RateLimit-Reset']

dtReset = datetime.utcfromtimestamp( ( epochNow + headerReset ) )
timeReset = dtReset.strftime('%H:%M:%S')

print("info API : %d/%d remaining - reset in %.1f mins [ %d secs ] at %s" % ( int(headerRemaining), int(headerLimit), float(headerReset)/60, int(headerReset), timeReset ) )

if responseStatus != 200:
    print("   error : response status != 200")

    match responseStatus:
        case 401:
            responseError = "     401 : API key passed expiry date"
        case 403:
            responseError = "     403 : API key not authorized to execute operation OR vehicle refused operation for user API key belongs to"
        case 422:
            responseError = "     422 : Vehicle lacks capability operation needs OR opperation currently disabled"
        case 429:
            responseError = "     429 : Rate limit for API key exceeded OR vehicle declined operation but can be retried later"
        case _:
            responseError = "     %d : Unknown response status" % ( responseStatus )

    print( responseError )

    # Influx - api
    senddata={}
    senddata["measurement"]="car"
    senddata["tags"]={}
    senddata["tags"]["source"]="docker skoda-influxdbv2"
    senddata["tags"]["origin"]="SkodaAPI"
    senddata["tags"]["vin"]=skodaapi_vin
    senddata["tags"]["host"]=host
    senddata["tags"]["info"]="api"
    senddata["fields"]={}
    senddata["fields"]["response"]=responseStatus
    senddata["time"]=epochNow
    write_influxdb()

    print("    exit : return status = 1" )
    sys.exit(1)

if debug:
    stringJSON = json.dumps(responseJSON, indent=4)
    print ( "  status :",responseStatus )
    print ( "   limit :",headerLimit )
    print ( "  remain :",headerRemaining )
    print ( "   reset :",headerReset )
    print ( "\nJSON\n"+stringJSON+"\n" )


# pass json
vin = responseJSON["vehicle"]["vin"]
name = responseJSON["vehicle"]["name"]

timeOdometer = responseJSON["vehicle"]["odometer"]["carCapturedTimestamp"]
odometer = responseJSON["vehicle"]["odometer"]["mileageInKm"]

timeFuel = responseJSON["vehicle"]["fuelStatus"]["carCapturedTimestamp"]
fuel = responseJSON["vehicle"]["fuelStatus"]["primaryEngineRange"]["currentFuelLevelInPercent"]
fuelRange = responseJSON["vehicle"]["fuelStatus"]["totalRangeInKm"]

timeState = responseJSON["vehicle"]["status"]["carCapturedTimestamp"]
status = responseJSON["vehicle"]["status"]["overall"]["reliableLockStatus"]
locked = responseJSON["vehicle"]["status"]["overall"]["locked"]
doorsLocked = responseJSON["vehicle"]["status"]["overall"]["doorsLocked"]
doors = responseJSON["vehicle"]["status"]["overall"]["doors"]
windows = responseJSON["vehicle"]["status"]["overall"]["windows"]
lights = responseJSON["vehicle"]["status"]["overall"]["lights"]
boot = responseJSON["vehicle"]["status"]["detail"]["trunk"]
bonnet = responseJSON["vehicle"]["status"]["detail"]["bonnet"]

parked = responseJSON["vehicle"]["parkingPosition"]["state"]
address = responseJSON["vehicle"]["parkingPosition"]["formattedAddress"]
longitude = responseJSON["vehicle"]["parkingPosition"]["gpsCoordinates"]["longitude"]
latitude = responseJSON["vehicle"]["parkingPosition"]["gpsCoordinates"]["latitude"]


# timestamp to iso and epoch
isoNow = dtNow.isoformat(sep=' ',timespec='seconds')

dtOdometer = datetime.strptime(timeOdometer, "%Y-%m-%dT%H:%M:%SZ")
isoOdometer = dtOdometer.isoformat(sep=' ',timespec='seconds')
epochOdometer = int( dtOdometer.timestamp())

dtFuel = datetime.strptime(timeFuel, "%Y-%m-%dT%H:%M:%SZ")
isoFuel = dtFuel.isoformat(sep=' ',timespec='seconds')
epochFuel = int( dtFuel.timestamp() )

dtState = datetime.strptime(timeState, "%Y-%m-%dT%H:%M:%SZ")
isoState = dtState.isoformat(sep=' ',timespec='seconds')
epochState = int( dtState.timestamp() )

# ago
ageMins = ( epochNow - epochOdometer ) / 60
ageHrs = ageMins / 60

# report to Docker log
print("odometer : %d km" % (odometer) )
print("captured :",timeOdometer )
print("data age : %.1f hrs [ %.0f mins ]" % ( ageHrs, ageMins ) )

if debug:
    print(" epoch-o :",epochOdometer )
    print(" epoch-f :",epochFuel )
    print(" epoch-s :",epochState )
    print(" epoch-n :",epochNow )
    print("   iso-o :",isoOdometer )
    print("   iso-f :",isoFuel )
    print("   iso-s :",isoState )
    print("   iso-n :",isoNow )
    print("    fuel :",fuel,"%" )
    print("   range :",fuelRange,"km" )
    print("   state :",parked )
    print(" address :",address )


# Influx - general
senddata={}
senddata["measurement"]="car"
senddata["tags"]={}
senddata["tags"]["source"]="docker skoda-influxdbv2"
senddata["tags"]["origin"]="SkodaAPI"
senddata["tags"]["vin"]=vin
senddata["tags"]["name"]=name
senddata["tags"]["host"]=host

# Influx - oddometer
senddata["tags"]["info"]="oddometer"
senddata["fields"]={}
senddata["fields"]["km"]=odometer
senddata["time"]=epochOdometer
write_influxdb()

# influx - park
del senddata["tags"]["info"]
del senddata["fields"]

senddata["tags"]["info"]="park"
senddata["fields"]={}
senddata["fields"]["state"]=parked
senddata["fields"]["address"]=address
senddata["fields"]["longitude"]=longitude
senddata["fields"]["latitude"]=latitude
write_influxdb()

# influx - fuel
del senddata["tags"]["info"]
del senddata["fields"]
del senddata["time"]

senddata["tags"]["info"]="fuel"
senddata["fields"]={}
senddata["fields"]["percent"]=fuel
senddata["fields"]["km"]=fuelRange
senddata["time"]=epochFuel
write_influxdb()

# influx - state
del senddata["tags"]["info"]
del senddata["fields"]
del senddata["time"]

senddata["tags"]["info"]="state"
senddata["fields"]={}
senddata["fields"]["locked"]=locked
senddata["fields"]["doors"]=doors
senddata["fields"]["windows"]=windows
senddata["fields"]["bonnet"]=bonnet
senddata["fields"]["boot"]=boot
senddata["time"]=epochState
write_influxdb()

# influx - api
del senddata["tags"]["name"]
del senddata["tags"]["info"]
del senddata["fields"]
del senddata["time"]

senddata["tags"]["info"]="api"
senddata["fields"]={}
senddata["fields"]["response"]=responseStatus
senddata["time"]=epochNow
write_influxdb()

# return OK
sys.exit(0)