A word of warning: to make use of this script you will have to connect a rs485 connector to your equipment. This means working on mains-voltage equipment so use your head. Always power down equipment before screwing them open and poking around in them. 
Also, all of this software is provided AS-IS with no implied warranty or liability under sections 15, and 16 of the GPL V3. So whatever happens, it is not my fault ;)

# Hewalex PCWU for Home Assistant
Communicates with Hewalex PCWU Heat pump, based on MQTT. 
Uses auto discovery protocal of Home Assistant, so it automatically adds the device with all sensors / switches to Home Assistant. 

## Hardware Prerequisites

Hewalex devices are equipped with empty RS485 connectors. 
This is basically a serial port. This script uses a 'serial for url' connection. 

You can buy a (cheap) wifi 2 rs485 or ethernet 2 rs485 device wich you attach to the rs485 port you want to interface with. And you need a piece of wire with 4 strands.

Remove the plastic case and open up the "fuse box". In here you will find a free rs485 connector. Remove it and screw in a 4 strand wire. Connect the wire to the rs485wifi device.
Make sure you connect them correctly. It is wise to measure ac and grnd to be sure!

In the controller, navigate to rs485 settings. Change baud rate to 38500, Actual address to 2 and Logic address to 2.

Setup the rs485-to-wifi device. Make sure baud settings match above settings.
It is probably wise to assign static ip-address. Take note of this.

## Software Prerequisities
Home Assistant
https://www.home-assistant.io/

## Using the script
just run the python script hewalex.py, or use the docker image.

### Parameters
All parameters are listed in the .ini file.
Modify them according to your needs when you are not using the pre-made docker image.

When you are using docker, make sure to set the environment variables. Or use the provided docker-compose and modify that accoriding to your setup.

**HA**

| Parameter | Value |
| ----------------------- | ----------- |
| MQTT_ip | 192.168.1.2
| MQTT_port | 1883
| MQTT_user | 
| MQTT_pass |

**Pcwu**

| Parameter | Value |
| ----------------------- | ----------- |
| Device_Pcwu_Address | IP of the RS485 to Wi-Fi device eg. 192.168.1.8
| Device_Pcwu_Port | Port of the RS485 to Wi-Fi device eg. 8899
| PCWU_Name | Name of the device for HA


## Acknowledgements

Based on
* https://github.com/Chibald/Hewalex2Mqtt
* https://github.com/mvdklip/Domoticz-Hewalex
* https://www.elektroda.pl/rtvforum/topic3499254.html 
* https://github.com/aelias-eu/hewalex-geco-protocol
