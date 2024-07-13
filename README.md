A word of warning: to make use of this script you will have to connect a rs485 connector to your equipment. This means working on mains-voltage equipment so use your head. Always power down equipment before screwing them open and poking around in them. 
Also, all of this software is provided AS-IS with no implied warranty or liability under sections 15, and 16 of the GPL V3. So whatever happens, it is not my fault ;)

# Hewalex 2 Mqtt

Mqtt gateway for hewalex heat pumps and solar pumps.

Solar Pump Hewalex / Geco controllers
G-422-P09
G-422-P09A

Heat Pump (Hewalex solmax)
PCWU 2.5kW
PCWU 3.0kW

Provides read and write access on mqtt topics. A typical use case is integration of hewalex solar pumps and/or heat pumps in Home Automation (HA) software.

This script is based on a domoticz plugin. So if you use domoticz a ready made plugin is available at: https://github.com/mvdklip/Domoticz-Hewalex

## Hardware Prerequisites

Hewalex devices are equipped with empty RS485 connectors. 
This is basically a serial port. This script uses a 'serial for url' connection. 

You can buy a (cheap) wifi 2 rs485 or ethernet 2 rs485 device wich you attach to the rs485 port you want to interface with. And you need a piece of wire with 4 strands.

### Heat pumps (PCWU) setup

Remove the plastic case and open up the "fuse box". In here you will find a free rs485 connector. Remove it and screw in a 4 strand wire. Connect the wire to the rs485wifi device.
Make sure you connect them correctly. It is wise to measure ac and grnd to be sure!

In the controller, navigate to rs485 settings. Change baud rate to 38500, Actual address to 2 and Logic address to 2.

Setup the rs485-to-wifi device. Make sure baud settings match above settings.
It is probably wise to assign static ip-address. Take note of this.

### Solar pumps (ZPS) setup

Remove G-422 controller from the casing. Connect the RS485 port on the backside of the G-422 controller to the wifi controller. 

## Software Prerequisities

You will need (and if you are reading this probably have) Home Automation software with/and MQTT broker.

Openhab
https://www.openhab.org/

Home Assistant
https://www.home-assistant.io/

But it'll work with any HA system that can process and send MQTT messages.

## Using the script
just run the python script hewalex2mqtt.py, or use the docker image.

### Parameters
All parameters are listed in the .ini file.
Modify them according to your needs when you are not using the pre-made docker image.

When you are using docker, make sure to set the environment variables. Or use the provided docker-compose and modify that accoriding to your setup.


**MQTT**
| Parameter | Value |
| ----------------------- | ----------- |
| MQTT_ip | 192.168.1.2
| MQTT_port | 1883
| MQTT_authentication | True
| MQTT_user | 
| MQTT_pass | 
| MQTT_GatewayDevice_Topic | HewaGate

**ZPS**
| Parameter | Value |
| ----------------------- | ----------- |
| Device_Zps_Enabled | False
| Device_Zps_Address | IP of the RS485 to Wi-Fi device eg. 192.168.1.7
| Device_Zps_Port | Port of the RS485 to Wi-Fi device eg. 8899
| Device_Zps_MqttTopic | SolarBoiler


**Pcwu**
| Parameter | Value |
| ----------------------- | ----------- |
| Device_Pcwu_Enabled | True
| Device_Pcwu_Address | IP of the RS485 to Wi-Fi device eg. 192.168.1.8
| Device_Pcwu_Port | Port of the RS485 to Wi-Fi device eg. 8899
| Device_Pcwu_MqttTopic | Heatpump


### Docker
A pre made docker image is available at https://hub.docker.com/r/chibald/hewalex2mqtt. 

```
version: '3.3'
services:

  hewalex2mqtt:
    image: chibald/hewalex2mqtt:latest
    network_mode: host
    environment:
      MQTT_ip: 192.168.1.2
      MQTT_port: 1883
      MQTT_authentication: 'False'
      MQTT_user: ''
      MQTT_pass: ''
      Device_Zps_Enabled: 'True'
      Device_Zps_Address: '192.168.1.7'
      Device_Zps_Port: 8899
      Device_Zps_MqttTopic: 'SolarBoiler'
      Device_Pcwu_Enabled: 'True'
      Device_Pcwu_Address: '192.168.1.8'
      Device_Pcwu_Port: '8899'
      Device_Pcwu_MqttTopic: 'Heatpump'
```

## MQTT Topics

There are 2 kinds of topics: state and command. 
Command topics (marked command) allow the sending of commands to topics to control equipment.

### Solar Pump
| Topic | Type | Description |
| ----------------------- | ----------- | ---------------------------
| SolarBoiler/date | date | Date
| SolarBoiler/time | time | Time
| SolarBoiler/T1 | temp | T1 (Collectors temp)
| SolarBoiler/T2 | temp | T2 (Tank bottom temp)
| SolarBoiler/T3 | temp | T3 (Air separator temp)
| SolarBoiler/T4 | temp | T4 (Tank top temp)
| SolarBoiler/T5 | temp | T5 (Boiler outlet temp)
| SolarBoiler/T6 | temp | T6
| SolarBoiler/CollectorPower | word | Collector Power (W)
| SolarBoiler/Consumption | fl10 | Consumption (W)
| SolarBoiler/CollectorActive | bool | Collector Active (True/False)
| SolarBoiler/FlowRate | fl10 | Flow Rate (l/min)
| SolarBoiler/CollectorPumpON | mask | None
| SolarBoiler/CirculationPumpON | mask | None
| SolarBoiler/CollectorPumpSpeed | word | Collector Pump Speed (0-15)
| SolarBoiler/TotalEnergy | fl10 | Total Energy (kWh)
| SolarBoiler/InstallationScheme | word | Installation Scheme (1-19)
| SolarBoiler/DisplayTimeout | word | Display Timeout (1-10 min)
| SolarBoiler/Command/DisplayTimeout | word | Display Timeout (1-10 min)
| SolarBoiler/DisplayBrightness | word | Display Brightness (1-10)
| SolarBoiler/Command/DisplayBrightness | word | Display Brightness (1-10)
| SolarBoiler/AlarmSoundEnabled | bool | Alarm Sound Enabled (True/False)
| SolarBoiler/Command/AlarmSoundEnabled | bool | Alarm Sound Enabled (True/False)
| SolarBoiler/KeySoundEnabled | bool | Key Sound Enabled (True/False)
| SolarBoiler/Command/KeySoundEnabled | bool | Key Sound Enabled (True/False)
| SolarBoiler/DisplayLanguage | word | Display Language (0=PL, 1=EN, 2=DE, 3=FR, 4=PT, 5=ES, 6=NL, 7=IT, 8=CZ, 9=SL, ...)
| SolarBoiler/Command/DisplayLanguage | word | Display Language (0=PL, 1=EN, 2=DE, 3=FR, 4=PT, 5=ES, 6=NL, 7=IT, 8=CZ, 9=SL, ...)
| SolarBoiler/FluidFreezingTemp | temp | Fluid Freezing Temp
| SolarBoiler/Command/FluidFreezingTemp | temp | Fluid Freezing Temp
| SolarBoiler/FlowRateNominal | fl10 | Flow Rate Nominal (l/min)
| SolarBoiler/Command/FlowRateNominal | fl10 | Flow Rate Nominal (l/min)
| SolarBoiler/FlowRateMeasurement | word | Flow Rate Measurement (0=Rotameter, 1=Electronic G916, 2=Electronic)
| SolarBoiler/Command/FlowRateMeasurement | word | Flow Rate Measurement (0=Rotameter, 1=Electronic G916, 2=Electronic)
| SolarBoiler/FlowRateWeight | f100 | Flow Rate Weight (imp/l)
| SolarBoiler/Command/FlowRateWeight | f100 | Flow Rate Weight (imp/l)
| SolarBoiler/HolidayEnabled | bool | Holiday Enabled (True/False)
| SolarBoiler/Command/HolidayEnabled | bool | Holiday Enabled (True/False)
| SolarBoiler/HolidayStartDay | word | Holiday Start Day
| SolarBoiler/Command/HolidayStartDay | word | Holiday Start Day
| SolarBoiler/HolidayStartMonth | word | Holiday Start Month
| SolarBoiler/Command/HolidayStartMonth | word | Holiday Start Month
| SolarBoiler/HolidayStartYear | word | Holiday Start Year
| SolarBoiler/Command/HolidayStartYear | word | Holiday Start Year
| SolarBoiler/HolidayEndDay | word | Holiday End Day
| SolarBoiler/Command/HolidayEndDay | word | Holiday End Day
| SolarBoiler/HolidayEndMonth | word | Holiday End Month
| SolarBoiler/Command/HolidayEndMonth | word | Holiday End Month
| SolarBoiler/HolidayEndYear | word | Holiday End Year
| SolarBoiler/Command/HolidayEndYear | word | Holiday End Year
| SolarBoiler/CollectorType | word | Collector Type (0=Flat, 1=Tube)
| SolarBoiler/Command/CollectorType | word | Collector Type (0=Flat, 1=Tube)
| SolarBoiler/CollectorPumpHysteresis | temp | Collector Pump Hysteresis (Difference between T1 and T2 to turn on collector pump)
| SolarBoiler/Command/CollectorPumpHysteresis | temp | Collector Pump Hysteresis (Difference between T1 and T2 to turn on collector pump)
| SolarBoiler/ExtraPumpHysteresis | temp | Extra Pump Hysteresis (Temp difference to turn on extra pump)
| SolarBoiler/Command/ExtraPumpHysteresis | temp | Extra Pump Hysteresis (Temp difference to turn on extra pump)
| SolarBoiler/CollectorPumpMaxTemp | temp | Collector Pump Max Temp (Maximum T2 temp to turn off collector pump)
| SolarBoiler/Command/CollectorPumpMaxTemp | temp | Collector Pump Max Temp (Maximum T2 temp to turn off collector pump)
| SolarBoiler/BoilerPumpMinTemp | word | Boiler Pump Min Temp (Minimum T5 temp to turn on boiler pump)
| SolarBoiler/Command/BoilerPumpMinTemp | word | Boiler Pump Min Temp (Minimum T5 temp to turn on boiler pump)
| SolarBoiler/HeatSourceMaxTemp | word | Heat Source Max Temp (Maximum T4 temp to turn off heat sources)
| SolarBoiler/Command/HeatSourceMaxTemp | word | Heat Source Max Temp (Maximum T4 temp to turn off heat sources)
| SolarBoiler/BoilerPumpMaxTemp | word | Boiler Pump Max Temp (Maximum T4 temp to turn off boiler pump)
| SolarBoiler/Command/BoilerPumpMaxTemp | word | Boiler Pump Max Temp (Maximum T4 temp to turn off boiler pump)
| SolarBoiler/PumpRegulationEnabled | bool | Pump Regulation Enabled (True/False)
| SolarBoiler/Command/PumpRegulationEnabled | bool | Pump Regulation Enabled (True/False)
| SolarBoiler/HeatSourceMaxCollectorPower | word | Heat Source Max Collector Power (Maximum collector power to turn off heat sources) (100-9900W)
| SolarBoiler/Command/HeatSourceMaxCollectorPower | word | Heat Source Max Collector Power (Maximum collector power to turn off heat sources) (100-9900W)
| SolarBoiler/CollectorOverheatProtEnabled | bool | Collector Overheat Protection Enabled (True/False)
| SolarBoiler/Command/CollectorOverheatProtEnabled | bool | Collector Overheat Protection Enabled (True/False)
| SolarBoiler/CollectorOverheatProtMaxTemp | temp | Collector Overheat Protection Max Temp (Maximum T2 temp for overheat protection)
| SolarBoiler/Command/CollectorOverheatProtMaxTemp | temp | Collector Overheat Protection Max Temp (Maximum T2 temp for overheat protection)
| SolarBoiler/CollectorFreezingProtEnabled | bool | Collector Freezing Protection Enabled (True/False)
| SolarBoiler/Command/CollectorFreezingProtEnabled | bool | Collector Freezing Protection Enabled (True/False)
| SolarBoiler/HeatingPriority | word | Heating Priority
| SolarBoiler/Command/HeatingPriority | word | Heating Priority
| SolarBoiler/LegionellaProtEnabled | bool | Legionella Protection Enabled (True/False)
| SolarBoiler/Command/LegionellaProtEnabled | bool | Legionella Protection Enabled (True/False)
| SolarBoiler/LockBoilerKWithBoilerC | bool | Lock Boiler K With Boiler C (True/False)
| SolarBoiler/Command/LockBoilerKWithBoilerC | bool | Lock Boiler K With Boiler C (True/False)
| SolarBoiler/NightCoolingEnabled | bool | Night Cooling Enabled (True/False)
| SolarBoiler/Command/NightCoolingEnabled | bool | Night Cooling Enabled (True/False)
| SolarBoiler/NightCoolingStartTemp | temp | Night Cooling Start Temp
| SolarBoiler/Command/NightCoolingStartTemp | temp | Night Cooling Start Temp
| SolarBoiler/NightCoolingStopTemp | temp | Night Cooling Stop Temp
| SolarBoiler/Command/NightCoolingStopTemp | temp | Night Cooling Stop Temp
| SolarBoiler/NightCoolingStopTime | word | Night Cooling Stop Time (hr)
| SolarBoiler/Command/NightCoolingStopTime | word | Night Cooling Stop Time (hr)
| SolarBoiler/TimeProgramCM-F | tprg | Time Program C M-F (True/False per hour of the day)
| SolarBoiler/Command/TimeProgramCM-F | tprg | Time Program C M-F (True/False per hour of the day)
| SolarBoiler/TimeProgramCSat | tprg | Time Program C Sat (True/False per hour of the day)
| SolarBoiler/Command/TimeProgramCSat | tprg | Time Program C Sat (True/False per hour of the day)
| SolarBoiler/TimeProgramCSun | tprg | Time Program C Sun (True/False per hour of the day)
| SolarBoiler/Command/TimeProgramCSun | tprg | Time Program C Sun (True/False per hour of the day)
| SolarBoiler/TimeProgramKM-F | tprg | Time Program K M-F (True/False per hour of the day)
| SolarBoiler/Command/TimeProgramKM-F | tprg | Time Program K M-F (True/False per hour of the day)
| SolarBoiler/TimeProgramKSat | tprg | Time Program K Sat (True/False per hour of the day)
| SolarBoiler/Command/TimeProgramKSat | tprg | Time Program K Sat (True/False per hour of the day)
| SolarBoiler/TimeProgramKSun | tprg | Time Program K Sun (True/False per hour of the day)
| SolarBoiler/Command/TimeProgramKSun | tprg | Time Program K Sun (True/False per hour of the day)
| SolarBoiler/CollectorPumpMinRev | word | Collector Pump Min Rev (rev/min)
| SolarBoiler/Command/CollectorPumpMinRev | word | Collector Pump Min Rev (rev/min)
| SolarBoiler/CollectorPumpMaxRev | word | Collector Pump Max Rev (rev/min)
| SolarBoiler/Command/CollectorPumpMaxRev | word | Collector Pump Max Rev (rev/min)
| SolarBoiler/CollectorPumpMinIncTime | word | Collector Pump Min Increase Time (s)
| SolarBoiler/Command/CollectorPumpMinIncTime | word | Collector Pump Min Increase Time (s)
| SolarBoiler/CollectorPumpMinDecTime | word | Collector Pump Min Decrease Time (s)
| SolarBoiler/Command/CollectorPumpMinDecTime | word | Collector Pump Min Decrease Time (s)
| SolarBoiler/CollectorPumpStartupSpeed | word | Collector Pump Startup Speed (1-15)
| SolarBoiler/Command/CollectorPumpStartupSpeed | word | Collector Pump Startup Speed (1-15)
| SolarBoiler/PressureSwitchEnabled | bool | Pressure Switch Enabled (True/False)
| SolarBoiler/Command/PressureSwitchEnabled | bool | Pressure Switch Enabled (True/False)
| SolarBoiler/TankOverheatProtEnabled | bool | Tank Overheat Protection Enabled (True/False)
| SolarBoiler/Command/TankOverheatProtEnabled | bool | Tank Overheat Protection Enabled (True/False)
| SolarBoiler/CirculationPumpEnabled | bool | Circulation Pump Enabled (True/False)
| SolarBoiler/Command/CirculationPumpEnabled | bool | Circulation Pump Enabled (True/False)
| SolarBoiler/CirculationPumpMode | word | Circulation Pump Mode (0=Discontinuous, 1=Continuous)
| SolarBoiler/Command/CirculationPumpMode | word | Circulation Pump Mode (0=Discontinuous, 1=Continuous)
| SolarBoiler/CirculationPumpMinTemp | temp | Circulation Pump Min Temp (Minimum T4 temp to turn on circulation pump)
| SolarBoiler/Command/CirculationPumpMinTemp | temp | Circulation Pump Min Temp (Minimum T4 temp to turn on circulation pump)
| SolarBoiler/CirculationPumpONTime | word | Circulation Pump ON Time (1-59 min)
| SolarBoiler/Command/CirculationPumpONTime | word | Circulation Pump ON Time (1-59 min)
| SolarBoiler/CirculationPumpOFFTime | word | Circulation Pump OFF Time (1-59 min)
| SolarBoiler/Command/CirculationPumpOFFTime | word | Circulation Pump OFF Time (1-59 min)
| SolarBoiler/TotalOperationTime | dwrd | Total Operation Time (min) - lives in config space but is status register
| SolarBoiler/Command/TotalOperationTime | dwrd | Total Operation Time (min) - lives in config space but is status register
| SolarBoiler/Reg320 | word | Unknown register - value changes constantly
| SolarBoiler/Command/Reg320 | word | Unknown register - value changes constantly

### Heat Pump
| Topic | Type | Description | 
| ----------------------- | ----------- | ---------------------------
| Heatpump/date | date | Date
| Heatpump/time | time | Time
| Heatpump/T1 | te10 | T1 (Ambient temp)
| Heatpump/T2 | te10 | T2 (Tank bottom temp)
| Heatpump/T3 | te10 | T3 (Tank top temp)
| Heatpump/T6 | te10 | T6 (HP water inlet temp)
| Heatpump/T7 | te10 | T7 (HP water outlet temp)
| Heatpump/T8 | te10 | T8 (HP evaporator temp)
| Heatpump/T9 | te10 | T9 (HP before compressor temp)
| Heatpump/T10 | te10 | T10 (HP after compressor temp)
| Heatpump/IsManual | bool | None
| Heatpump/FanON | mask | None
| Heatpump/CirculationPumpON | mask | None
| Heatpump/HeatPumpON | mask | None
| Heatpump/CompressorON | mask | None
| Heatpump/HeaterEON | mask | None
| Heatpump/EV1 | word | Expansion valve
| Heatpump/WaitingStatus | word |  0 when available for operation, 2 when disabled through register 304
| Heatpump/InstallationScheme | word | Installation Scheme (1-9)
| Heatpump/HeatPumpEnabled | bool | Heat Pump Enabled (True/False)
| Heatpump/Command/HeatPumpEnabled | bool | Heat Pump Enabled (True/False)
| Heatpump/TapWaterSensor | word | Temp. sensor controlling heat pump operation [T2,T3,T7, factory setting T2]
| Heatpump/Command/TapWaterSensor | word | Temp. sensor controlling heat pump operation [T2,T3,T7, factory setting T2]
| Heatpump/TapWaterTemp | te10 | HUW temperature for heat pump [10-60°C, factory setting 50°C]
| Heatpump/Command/TapWaterTemp | te10 | HUW temperature for heat pump [10-60°C, factory setting 50°C]
| Heatpump/TapWaterHysteresis | te10 | Heat pump start-up hysteresis [2-10°C, factory setting 5°C]
| Heatpump/Command/TapWaterHysteresis | te10 | Heat pump start-up hysteresis [2-10°C, factory setting 5°C]
| Heatpump/AmbientMinTemp | te10 | Minimum ambient temperature (T1) [-10-10°C]
| Heatpump/Command/AmbientMinTemp | te10 | Minimum ambient temperature (T1) [-10-10°C]
| Heatpump/TimeProgramHPM-F | tprg | Time Program HP M-F (True/False per hour of the day)
| Heatpump/Command/TimeProgramHPM-F | tprg | Time Program HP M-F (True/False per hour of the day)
| Heatpump/TimeProgramHPSat | tprg | Time Program HP Sat (True/False per hour of the day)
| Heatpump/Command/TimeProgramHPSat | tprg | Time Program HP Sat (True/False per hour of the day)
| Heatpump/TimeProgramHPSun | tprg | Time Program HP Sun (True/False per hour of the day)
| Heatpump/Command/TimeProgramHPSun | tprg | Time Program HP Sun (True/False per hour of the day)
| Heatpump/AntiFreezingEnabled | bool | Function protecting against freezing [YES/NO], factory setting YES
| Heatpump/Command/AntiFreezingEnabled | bool | Function protecting against freezing [YES/NO], factory setting YES
| Heatpump/WaterPumpOperationMode | word | Water Pump Operation Mode (0=Continuous, 1=Synchronous)
| Heatpump/Command/WaterPumpOperationMode | word | Water Pump Operation Mode (0=Continuous, 1=Synchronous)
| Heatpump/FanOperationMode | word | Fan Operation Mode (0=Max, 1=Min, 2=Day/Night), factory MAX
| Heatpump/Command/FanOperationMode | word | Fan Operation Mode (0=Max, 1=Min, 2=Day/Night), factory MAX
| Heatpump/DefrostingInterval | word | Defrosting cycle start-up delay [30-90 min., factory setting 45 min.]
| Heatpump/Command/DefrostingInterval | word | Defrosting cycle start-up delay [30-90 min., factory setting 45 min.]
| Heatpump/DefrostingStartTemp | te10 | Temperature activating defrosting [-30 - 0°C, factory setting -7°C]
| Heatpump/Command/DefrostingStartTemp | te10 | Temperature activating defrosting [-30 - 0°C, factory setting -7°C]
| Heatpump/DefrostingStopTemp | te10 | Temperature finishing defrosting [2-30°C, factory setting 13°C]
| Heatpump/Command/DefrostingStopTemp | te10 | Temperature finishing defrosting [2-30°C, factory setting 13°C]
| Heatpump/DefrostingMaxTime | word | Maximum defrosting duration [1-12 min., factory setting 8 min.]
| Heatpump/Command/DefrostingMaxTime | word | Maximum defrosting duration [1-12 min., factory setting 8 min.]
| Heatpump/HeaterEEnabled | bool | Electrical heater activation (True/False)
| Heatpump/Command/HeaterEEnabled | bool | Electrical heater activation (True/False)
| Heatpump/HeaterEHPONTemp | te10 | HUW temperature for electric heater if heat pump is on  [??°C, factory setting 45°C]
| Heatpump/Command/HeaterEHPONTemp | te10 | HUW temperature for electric heater if heat pump is on [??°C, factory setting 55°C]
| Heatpump/HeaterEHPOFFTemp | te10 | HUW temperature for electric heater if heat pump is off [??°C, factory setting ??°C]
| Heatpump/Command/HeaterEHPOFFTemp | te10 | HUW temperature for electric heater if heat pump is off [??°C, factory setting 50°C]
| Heatpump/HeaterEBlocked | bool | Electric Heater blocked when HP is on (True/False)
| Heatpump/Command/HeaterEBlocked | bool | Electric Heater blocked when HP is on (True/False)
| Heatpump/HeaterETimeProgramM-F | bool | Heater E Time Program M-F (True/False per hour of the day)
| Heatpump/Command/HeaterETimeProgramM-F | ?? | Heater E Time Program M-F (True/False per hour of the day)
| Heatpump/HeaterETimeProgramSat | ?? | Heater E Time Program Sat (True/False per hour of the day)
| Heatpump/Command/HeaterETimeProgramSat | ?? | Heater E Time Program Sat (True/False per hour of the day)
| Heatpump/HeaterETimeProgramSun | ?? | Heater E Time Program Sun (True/False per hour of the day)
| Heatpump/Command/HeaterETimeProgramSun | bool | Heater E Time Program Sun (True/False per hour of the day)
| Heatpump/AntiLegionellaEnabled | bool | Anti-Legionella Enabled (True/False)
| Heatpump/Command/AntiLegionellaEnabled | bool | Anti-Legionella Enabled (True/False)
| Heatpump/AntiLegionellaUseHeaterE | bool | Anti-Legionella Use Heater E (True/False)
| Heatpump/Command/AntiLegionellaUseHeaterE | bool | Anti-Legionella Use Heater E (True/False)
| Heatpump/AntiLegionellaUseHeaterP | bool | Anti-Legionella Use Heater P (True/False)
| Heatpump/Command/AntiLegionellaUseHeaterP | bool | Anti-Legionella Use Heater P (True/False)
| Heatpump/ExtControllerHPOFF | bool | Ext Controller Heat pump deactivation (True/False)
| Heatpump/Command/ExtControllerHPOFF | bool | Ext Controller Heat pump deactivation (True/False)
| Heatpump/ExtControllerHeaterEOFF | bool | Ext Controller Electric heater deactivation (True/False)
| Heatpump/Command/ExtControllerHeaterEOFF | bool | Ext Controller Electric heater deactivation (True/False)

### Examples
Turn off heat pump
`Heatpump/Command/HeatPumpEnabled False`

Change T2 temperature setting to 52°C
`Heatpump/Command/TapWaterTemp 52`

etc. etc.

## Acknowledgements

Based on
* https://github.com/mvdklip/Domoticz-Hewalex
* https://www.elektroda.pl/rtvforum/topic3499254.html 
* https://github.com/aelias-eu/hewalex-geco-protocol
