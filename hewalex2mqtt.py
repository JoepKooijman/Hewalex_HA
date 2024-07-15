import os
import threading
import configparser
import serial
from hewalex_geco.devices import PCWU
import paho.mqtt.client as mqtt
import logging
import sys

# polling interval
get_status_interval = 30.0

# Controller (Master)
conHardId = 1
conSoftId = 1

# ZPS (Slave)
devHardId = 2
devSoftId = 2

#mqtt
flag_connected_mqtt = 0
MessageCache = {}

# logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s :: %(name)s :: %(levelname)s :: %(message)s')
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.DEBUG)
logger.addHandler(stream_handler)

# Start
logger.info('Starting Hewalex 2 Mqtt')

# Read Configs
def initConfiguration():
    logger.info("reading config")
    config_file = os.path.join(os.path.dirname(__file__), 'hewalex2mqttconfig.ini')
    config = configparser.ConfigParser()
    config.read(config_file)
    # Mqtt
    global _MQTT_ip
    if (os.getenv('MQTT_ip') != None):        
        _MQTT_ip = os.getenv('MQTT_ip')
    else:
        _MQTT_ip = config['MQTT']['MQTT_ip']
    global _MQTT_port
    if (os.getenv('MQTT_port') != None):        
        _MQTT_port = int(os.getenv('MQTT_port'))
    else:
        _MQTT_port = config.getint('MQTT', 'MQTT_port')
    global _MQTT_authentication
    if (os.getenv('MQTT_authentication') != None):        
        _MQTT_authentication = os.getenv('MQTT_authentication') == "True"
    else:
        _MQTT_authentication = config.getboolean('MQTT','MQTT_authentication')
    global _MQTT_user
    if (os.getenv('MQTT_user') != None):        
        _MQTT_user = os.getenv('MQTT_user')
    else:
        _MQTT_user = config['MQTT']['MQTT_user']
    global _MQTT_pass
    if (os.getenv('MQTT_pass') != None):        
        _MQTT_pass = os.getenv('MQTT_pass')
    else:
        _MQTT_pass = config['MQTT']['MQTT_pass']

    # PCWU Device
    global _Device_Pcwu_Enabled
    if (os.getenv('Device_Pcwu_Enabled') != None):        
        _Device_Pcwu_Enabled = os.getenv('Device_Pcwu_Enabled') == "True"
    else:
        _Device_Pcwu_Enabled = config.getboolean('Pcwu', 'Device_Pcwu_Enabled')

    global _Device_Pcwu_Address
    if (os.getenv('_Device_Pcwu_Address') != None):        
        _Device_Pcwu_Address = os.getenv('Device_Pcwu_Address')
    else:
        _Device_Pcwu_Address = config['Pcwu']['Device_Pcwu_Address']        
    global _Device_Pcwu_Port
    if (os.getenv('Device_Pcwu_Port') != None):        
        _Device_Pcwu_Port = os.getenv('Device_Pcwu_Port')
    else:
        _Device_Pcwu_Port = config['Pcwu']['Device_Pcwu_Port']

    global _Device_Pcwu_MqttTopic
    if (os.getenv('Device_Pcwu_MqttTopic') != None):        
        _Device_Pcwu_MqttTopic = os.getenv('Device_Pcwu_MqttTopic')
    else:
        _Device_Pcwu_MqttTopic = config['Pcwu']['Device_Pcwu_MqttTopic']

def start_mqtt():
    global client
    logger.info('Connection in progress to the Mqtt broker (IP:' +_MQTT_ip + ' PORT:'+str(_MQTT_port)+')')
    client = mqtt.Client()
    if _MQTT_authentication:
        logger.info('Mqtt authentication enabled')
        client.username_pw_set(username=_MQTT_user, password=_MQTT_pass)
    client.on_connect = on_connect_mqtt
    client.on_disconnect = on_disconnect_mqtt
    client.on_message = on_message_mqtt        
    client.connect(_MQTT_ip, _MQTT_port)  
    if (_Device_Pcwu_Enabled):
        logger.info('subscribed to : ' + _Device_Pcwu_MqttTopic + '/Command/#')    
        client.subscribe(_Device_Pcwu_MqttTopic + '/Command/#', qos=1)
    client.loop_start()

def on_connect_mqtt(client, userdata, flags, r):
    logger.info("Mqtt: Connected to broker. ")
    global flag_connected_mqtt
    flag_connected_mqtt = 1

def on_disconnect_mqtt(client, userdata, rc):
    logger.info("Mqtt: disconnected. ")
    global flag_connected_mqtt
    flag_connected_mqtt = 0

def on_message_mqtt(client, userdata, message):    
    try:        
        payload = str(message.payload.decode())
        topic = str(message.topic)
        arr = topic.split('/')
        # PCWU Command 
        if len(arr) == 3 and arr[0] == _Device_Pcwu_MqttTopic and arr[1] == 'Command':            
            command = arr[2]
            logger.info('Recieved PCWU command ' + topic)
            writePcwuConfig(command, payload)
        else:
            logger.info('cannot process message on topic ' + topic)

    except Exception as e:
        logger.info('Exception in on_message_mqtt: '+ str(e))

def on_message_serial(obj, h, sh, m):
    try:    
        if flag_connected_mqtt != 1:
            return False
        
        global MessageCache
        topic = _Device_Zps_MqttTopic
        if isinstance(obj, PCWU):
            topic = _Device_Pcwu_MqttTopic
    
        if sh["FNC"] == 0x50:
            mp = obj.parseRegisters(sh["RestMessage"], sh["RegStart"], sh["RegLen"])        
            for item in mp.items():
                if isinstance(item[1], dict): # skipping dictionaries (time program) 
                    continue
                key = topic + '/' + str(item[0])
                val = str(item[1])
                if key not in MessageCache or MessageCache[key] != val:
                    MessageCache[key] = val
                    logger.info(key + " " + val)
                    client.publish(key, val)

    except Exception as e:
        logger.info('Exception in on_message_serial: '+ str(e))

def device_readregisters_enqueue():
    """Get device status every x seconds"""
    logger.info('Get device status')
    threading.Timer(get_status_interval, device_readregisters_enqueue).start()
    if _Device_Zps_Enabled:        
        readZPS()
        #readZPSConfig() dont care fot this ona ATM
    if _Device_Pcwu_Enabled:        
        readPCWU()
        readPcwuConfig()

def readPCWU():    
    ser = serial.serial_for_url("socket://%s:%s" % (_Device_Pcwu_Address, _Device_Pcwu_Port))
    dev = PCWU(conHardId, conSoftId, devHardId, devSoftId, on_message_serial)        
    dev.readStatusRegisters(ser)    
    ser.close()   

def readPcwuConfig():    
    ser = serial.serial_for_url("socket://%s:%s" % (_Device_Pcwu_Address, _Device_Pcwu_Port))
    dev = PCWU(conHardId, conSoftId, devHardId, devSoftId, on_message_serial)            
    dev.readConfigRegisters(ser)
    ser.close()

def writePcwuConfig(registerName, payload):    
    ser = serial.serial_for_url("socket://%s:%s" % (_Device_Pcwu_Address, _Device_Pcwu_Port))
    dev = PCWU(conHardId, conSoftId, devHardId, devSoftId, on_message_serial)            
    dev.write(ser, registerName, payload)
    ser.close()

def printPcwuMqttTopics():        
    print('| Topic | Type | Description | ')
    print('| ----------------------- | ----------- | ---------------------------')
    dev = PCWU(conHardId, conSoftId, devHardId, devSoftId, on_message_serial)
    for k, v in dev.registers.items():
        if isinstance(v['name'] , list):
            for i in v['name']:
                if i:
                    print('| ' + _Device_Pcwu_MqttTopic + '/' + str(i) + ' | ' + v['type'] + ' | ' + str(v.get('desc')))
        else:
            print('| ' +_Device_Pcwu_MqttTopic + '/' + str(v['name'])+ ' | ' + v['type'] + ' | ' + str(v.get('desc')))
        if k > dev.REG_CONFIG_START:          
            print('| ' + _Device_Pcwu_MqttTopic + '/Command/' + str(v['name']) + ' | ' + v.get('type') + ' | ' + str(v.get('desc')))

if __name__ == "__main__":
    initConfiguration()
    # for generating topic list in readme
    # printPcwuMqttTopics()
    # printZPSMqttTopics()
    start_mqtt()
    device_readregisters_enqueue()
