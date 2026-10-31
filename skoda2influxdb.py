#!/usr/bin/env python3
# encoding=utf-8

# TODO : read key from file

# pip3 install pytz influxdb_client requests
# python3 -c "help('modules')"

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
skodaapi_vin = os.getenv("SKODA_VIN")
skodaapi_key = os.getenv("SKODA_KEY")


# file key - override
keyFile = path.abspath(path.join(path.dirname(path.abspath(__file__)), "apikey"))

if os.path.exists(keyFile):
    FILE = open(keyFile, "r")
    skodaapi_key = FILE.read().rstrip()
    FILE.close()
    print ( " keyFile: "+skodaapi_key )
exit()


# hard encoded envionment varables for testing
if os.path.exists('private-skoda.py'):
    print("  incl: private-skoda.py")
    exec(compile(source=open('private-skoda.py').read(), filename='private-skoda.py', mode='exec'))
    debug = True


# report debug status
if debug:
	print ( " debug: TRUE" )
else:
	print ( " debug: FALSE" )
	


# influxDBv2
if influxdb2_ssl_str:
    influxdb2_url="https://" + influxdb2_host + ":" + str(influxdb2_port)
else:
    influxdb2_url="http://" + influxdb2_host + ":" + str(influxdb2_port)

if debug:
	print ( "influx: "+influxdb2_url )
	print ( "bucket: "+influxdb2_bucket )
	
if influxdb2_ssl_verify:
	print ( "verify: True" )
	client = InfluxDBClient(url=influxdb2_url, token=influxdb2_token, org=influxdb2_org, verify_ssl=True)
else:
	print ( "verify: False" )
	client = InfluxDBClient(url=influxdb2_url, token=influxdb2_token, org=influxdb2_org, verify_ssl=False)

write_api = client.write_api(write_options=SYNCHRONOUS)

def write_influxdb():
    if debug:
        print ("INFLUX: "+influxdb2_bucket)
        print (json.dumps(senddata,indent=4))
        print()
    write_api.write(bucket=influxdb2_bucket, org=influxdb2_org, record=[senddata], write_precision="s")






# Get Data for VIN via Skoda API using key
print("Running Skoda API")

apiHEADR = { "X-API-Key" : skodaapi_key }
skodaURL = "https://public.api.connect.skoda-auto.cz/api/v1/vehicles/"+skodaapi_vin
#apiQUERY = {'include': ['status', 'odometer', 'fuelStatus', 'parkingPosition']}
apiQUERY = {}


if debug:
    print()
    print ( "input vin: "+skodaapi_vin )
    print ( "input key: "+skodaapi_key )
    print ( "input url: "+skodaURL )
    #print ( "hdr: " )
    #[ print ( f"{key}: {value}") for key, value in apiHEADR.items() ]
    #print ( "qry: " )
   # [ print ( f"{key}: {value}") for key, value in apiQUERY.items() ]

rawResponse = requests.get(skodaURL, params=apiQUERY, headers=apiHEADR)
statusResponse = rawResponse.status_code
jsonResponse = rawResponse.json()

if debug:
    jsonString = json.dumps(jsonResponse, indent=4)
    print ( "     url : ",rawResponse.url )
    print ( "response : ",statusResponse )
    print ( "    json :\n"+jsonString )
    print()

if statusResponse != 200:
    print ( "error : ",statusResponse )
    exit()

results = jsonResponse




# Basic values
vin = results["vehicle"]["vin"]
name = results["vehicle"]["name"]

timeOddo = results["vehicle"]["odometer"]["carCapturedTimestamp"]
odometer = results["vehicle"]["odometer"]["mileageInKm"]

timeFuel = results["vehicle"]["fuelStatus"]["carCapturedTimestamp"]
fuel = results["vehicle"]["fuelStatus"]["primaryEngineRange"]["currentFuelLevelInPercent"]
fuelRange = results["vehicle"]["fuelStatus"]["totalRangeInKm"]

timeState = results["vehicle"]["status"]["carCapturedTimestamp"]
status = results["vehicle"]["status"]["overall"]["reliableLockStatus"]
locked = results["vehicle"]["status"]["overall"]["locked"]
doorsLocked = results["vehicle"]["status"]["overall"]["doorsLocked"]
doors = results["vehicle"]["status"]["overall"]["doors"]
windows = results["vehicle"]["status"]["overall"]["windows"]
lights = results["vehicle"]["status"]["overall"]["lights"]
boot = results["vehicle"]["status"]["detail"]["trunk"]
bonnet = results["vehicle"]["status"]["detail"]["bonnet"]

parked = results["vehicle"]["parkingPosition"]["state"]
address = results["vehicle"]["parkingPosition"]["formattedAddress"]
longitude = results["vehicle"]["parkingPosition"]["gpsCoordinates"]["longitude"]
latitude = results["vehicle"]["parkingPosition"]["gpsCoordinates"]["latitude"]



# timestamp to epoch
dtOddo = datetime.strptime(timeOddo, "%Y-%m-%dT%H:%M:%SZ")
isoOddo = dtOddo.isoformat()
epochOddo = int( dtOddo.timestamp())

dtFuel = datetime.strptime(timeFuel, "%Y-%m-%dT%H:%M:%SZ")
isoFuel = dtFuel.isoformat()
epochFuel = int( dtFuel.timestamp() )

dtState = datetime.strptime(timeState, "%Y-%m-%dT%H:%M:%SZ")
isoState = dtState.isoformat()
epochState = int( dtState.timestamp() )

# Print results to Docker logs
print(" odometer %d km" % (odometer) )
print("     time",timeOddo )


if debug:
    print("  epoch-o",epochOddo )
    print("  epoch-f",epochFuel )
    print("  epoch-s",epochState )
    print("    iso-o",isoOddo )
    print("    iso-f",isoFuel )
    print("    iso-s",isoState )
    print("     fuel",fuel )
    print("    range",fuelRange )
    print("    state",parked )
    print("  address",address )
    print()


# Influx - oddometer
senddata={}

senddata["measurement"]="car"
senddata["tags"]={}
senddata["tags"]["source"]="docker skoda-influxdbv2"
senddata["tags"]["origin"]="SkodaAPI"
senddata["tags"]["vin"]=vin
senddata["tags"]["name"]=name
senddata["tags"]["host"]=host

senddata["tags"]["info"]="oddometer"
senddata["fields"]={}
senddata["fields"]["km"]=odometer
senddata["time"]=epochOddo
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
