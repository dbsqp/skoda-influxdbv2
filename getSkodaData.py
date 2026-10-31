#!/usr/bin/env python3
# encoding=utf-8

# TODO : read key from file
# TODO : timestamp from data not push

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

# hard encoded envionment varables
debug = True
influxdb2_ssl = True
influxdb2_ssl_verify = False
influxdb2_bucket = "TST"
influxdb2_host = "10.0.0.10"
influxdb2_token = "WYfX6nOfy7yAyv9_q9cuwANJbGA3YhYzOt1vPsovBOkrdn5Rj7M-yxKzRT-Fvx7zSY1FA6uIkpEZotkl5BzDbg=="
skodaapi_vin = "TMBLT8NX6VY011506"
skodaapi_key = "msk_2fbbeed39725_rQYgYgyCSXWmB1T5xIzth0tBShvW5QjpelP7gfJX3xx"





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
name = results["vehicle"]["name"]
timestamp = results["vehicle"]["fuelStatus"]["carCapturedTimestamp"]
fuel = results["vehicle"]["fuelStatus"]["primaryEngineRange"]["currentFuelLevelInPercent"]
fuelRange = results["vehicle"]["fuelStatus"]["totalRangeInKm"]
odometer = results["vehicle"]["odometer"]["mileageInKm"]
locked = results["vehicle"]["status"]["overall"]["locked"]
doorsLocked = results["vehicle"]["status"]["overall"]["doorsLocked"]
doors = results["vehicle"]["status"]["overall"]["doors"]
windows = results["vehicle"]["status"]["overall"]["windows"]
lights = results["vehicle"]["status"]["overall"]["lights"]
status = results["vehicle"]["status"]["overall"]["reliableLockStatus"]
boot = results["vehicle"]["status"]["detail"]["trunk"]
bonnet = results["vehicle"]["status"]["detail"]["bonnet"]
parked = results["vehicle"]["parkingPosition"]["state"]
address = results["vehicle"]["parkingPosition"]["formattedAddress"]
longitude = results["vehicle"]["parkingPosition"]["gpsCoordinates"]["longitude"]
latitude = results["vehicle"]["parkingPosition"]["gpsCoordinates"]["latitude"]
vin = results["vehicle"]["vin"]
name = results["vehicle"]["name"]


# Print results to Docker logs
print("odometer %d km" % (odometer) )
print("    time",timestamp )

if debug:
    print("    fuel",fuel)
    print("   range",fuelRange)
    print("   state",parked)
    print(" address",address)
    print()


# state
senddata={}

senddata["measurement"]="car"
senddata["tags"]={}
senddata["tags"]["source"]="docker skoda-influxdbv2"
senddata["tags"]["origin"]="SkodaAPI"
senddata["tags"]["vin"]=vin
senddata["tags"]["name"]=name
senddata["tags"]["host"]=host
senddata["tags"]["info"]="state"
senddata["fields"]={}
senddata["fields"]["odometer"]=odometer
senddata["fields"]["fuel"]=fuel
senddata["fields"]["range"]=fuelRange

if debug:
    print ("INFLUX: "+influxdb2_bucket)
    print (json.dumps(senddata,indent=4))
    print()
write_api.write(bucket=influxdb2_bucket, org=influxdb2_org, record=[senddata])


# location
senddata={}

senddata["measurement"]="car"
senddata["tags"]={}
senddata["tags"]["source"]="docker skoda-influxdbv2"
senddata["tags"]["origin"]="SkodaAPI"
senddata["tags"]["vin"]=vin
senddata["tags"]["name"]=name
senddata["tags"]["host"]=host
senddata["tags"]["info"]="location"
senddata["fields"]={}
senddata["fields"]["state"]=parked
senddata["fields"]["address"]=address
senddata["fields"]["longitude"]=longitude
senddata["fields"]["latitude"]=latitude

if debug:
    print ("INFLUX: "+influxdb2_bucket)
    print (json.dumps(senddata,indent=4))
    print()
write_api.write(bucket=influxdb2_bucket, org=influxdb2_org, record=[senddata])


# security
senddata={}

senddata["measurement"]="car"
senddata["tags"]={}
senddata["tags"]["source"]="docker skoda-influxdbv2"
senddata["tags"]["origin"]="SkodaAPI"
senddata["tags"]["vin"]=vin
senddata["tags"]["name"]=name
senddata["tags"]["host"]=host
senddata["tags"]["info"]="security"
senddata["fields"]={}
senddata["fields"]["locked"]=locked
senddata["fields"]["doors"]=doors
senddata["fields"]["windows"]=windows
senddata["fields"]["bonnet"]=bonnet
senddata["fields"]["boot"]=boot

if debug:
    print ("INFLUX: "+influxdb2_bucket)
    print (json.dumps(senddata,indent=4))
    print()
write_api.write(bucket=influxdb2_bucket, org=influxdb2_org, record=[senddata])
