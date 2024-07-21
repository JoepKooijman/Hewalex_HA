from crc import *
from ha_mqtt_discoverable import Settings, DeviceInfo
from ha_mqtt_discoverable.sensors import BinarySensor, BinarySensorInfo, Sensor, SensorInfo, Switch, SwitchInfo, Number, NumberInfo
import configparser
import serial
from paho.mqtt.client import Client, MQTTMessage
from threading import Timer

# Based on work by krzysztof1111111111
# https://www.elektroda.pl/rtvforum/topic3499254.html

class PCWU:
    def __init__(self, config_file,logger):
        # retrieve configuration
        config = configparser.ConfigParser()
        config.read(config_file)
        MQTT_ip = config['HA']['MQTT_ip']
        MQTT_port = config.getint('HA', 'MQTT_port')
        MQTT_user = config['HA']['MQTT_user']
        MQTT_pass = config['HA']['MQTT_pass']
        self.PCWU_Address = config['PCWU']['PCWU_Address']
        self.PCWU_Port = config['PCWU']['PCWU_Port']
        self.PCWU_Name = config['PCWU']['PCWU_Name']
        self.status_interval = 30
        self.conHardId = 1 # G-426 controller - physical address
        self.conSoftId = 1 # G-426 controller - logical address
        self.devHardId = 2 # Hewalex device - physical address
        self.devSoftId = 2 # Hewalex device - logical address
        self.logger = logger
        mqttconnected = False

        while not mqttconnected:
            try:
                self.mqtt_settings = Settings.MQTT(host=MQTT_ip, port=MQTT_port, username=MQTT_user, password=MQTT_pass)
                # define device information
                self.device_info = DeviceInfo(name="Hewalex", identifiers="hewalex_pcwu",model="PCWU",manufacturer="Hewalex")

                # initialize sensors
                for register,data in self.StatusRegisters.items():
                    if data['ha_type'] == 'sensor':
                        sensor_info = SensorInfo(name=data["name"], unit_of_measurement=data["unit"], unique_id=data["id"], device=self.device_info)
                        settings = Settings(mqtt=self.mqtt_settings, entity=sensor_info)
                        data["sensor"] = Sensor(settings)
                    elif data['ha_type'] == 'binarysensor':
                        sensor_info = BinarySensorInfo(name=data["name"], unique_id=data["id"], device=self.device_info)
                        settings = Settings(mqtt=self.mqtt_settings, entity=sensor_info)
                        data["sensor"] = BinarySensor(settings)
                    elif data['ha_type'] == 'binarysensors':
                        for idx in range(len(data["id"])):
                            if data["id"][idx] is not None:
                                sensor_info = BinarySensorInfo(name=data["name"][idx], unique_id=data["id"][idx], device=self.device_info)
                                settings = Settings(mqtt=self.mqtt_settings, entity=sensor_info)
                                data["sensor"][idx] = BinarySensor(settings)

                # initialize configurations
                for register, data in self.ConfigRegisters.items():
                    if data['ha_type'] == 'switch':
                        switch_info = SwitchInfo(name=data["name"], unique_id=data["id"], device=self.device_info)
                        settings = Settings(mqtt=self.mqtt_settings, entity=switch_info)
                        data["switch"] = Switch(settings, self.HACallbackSwitch, data["id"])
                    elif data['ha_type'] == 'number':
                        number_info = NumberInfo(name=data["name"],unique_id=data["id"],min=int(data["options"][0])/10, max=int(data["options"][-1])/10, device=self.device_info)
                        settings = Settings(mqtt=self.mqtt_settings, entity=number_info)
                        data["number"] = Number(settings, self.HACallbackNumber, data["id"])
                logger.info("--- Initialized sensors")
                mqttconnected = True
            except Exception as err:
                self.logger.info("Error occured during initialization of sensors to HA")
                self.logger.info("An exception occurred:" + str(err))
        # start thread to update sensors and listen to activities
        self.run()

    def run(self):
        self.is_running = False
        self.start()
        self.UpdateStatus()
    def start(self):
        if not self.is_running:
            self.timer = Timer(self.status_interval, self.run)
            self.timer.start()
            self.is_running = True
    def UpdateStatus(self):
        try:
            # Poll status of sensors
            self.ser = serial.serial_for_url("socket://%s:%s" % (self.PCWU_Address, self.PCWU_Port))
            self.ser.close()
            self.ser.open()
            self.readStatusRegisters(self.ser)
            self.readConfigRegisters(self.ser)
            self.ser.close()
        except Exception as err:
            self.logger.info("An exception occurred:"+str(err))

    def parseHardHeader(self, m):
        if len(m) < 8:
            raise Exception("Too short message")
        calcCrc = crc8(m[:7])
        return {
            "StartByte": m[0],
            "To": m[1],
            "From": m[2],
            "ConstBytes": (m[5] << 16) | (m[4] << 8) | m[3],
            "Payload": m[6],
            "CRC8": m[7],
            "CalcCRC8": calcCrc
        }

    def validateHardHeader(self, h):
        if h["StartByte"] != 0x69:
            raise Exception("Invalid Start Byte")
        if h["CRC8"] != h["CalcCRC8"]:
            raise Exception("Invalid Hard CRC8")
        if h["ConstBytes"] != 0x84:
            raise Exception("Invalid Const Bytes")
        if h["From"] != self.conHardId and h["From"] != self.devHardId:
            raise Exception("Invalid From Hard Address: " + str(h["From"]))
        if h["To"] != self.conHardId and h["To"] != self.devHardId:
            raise Exception("Invalid To Hard Address: " + str(h["To"]))
        if h["To"] == h["From"]:
            raise Exception("From and To Hard Address Equal")

    def getWord(self, w):
        return (w[1] << 8) | w[0]

    def getWordReverse(self, w):
        return (w[0] << 8) | w[1]

    def getDWord(self, w):
        return (w[3] << 24) | (w[2] << 16) | (w[1] << 8) | w[0]

    def parseSoftHeader(self, h, m):
        if len(m) != h["Payload"]:
            raise Exception("Invalid soft message len")
        if len(m) < 12:
            raise Exception("Too short soft message")
        calcCrc = crc16(m[:h["Payload"] - 2])
        return {
            "To": self.getWord(m[0:]),
            "From": self.getWord(m[2:]),
            "FNC": m[4],
            "ConstByte": self.getWord(m[5:]),
            "RegLen": m[7],
            "RegStart": self.getWord(m[8:]),
            "RestMessage": m[10:h["Payload"] - 2],
            "CRC16": self.getWordReverse(m[h["Payload"] - 2:]),
            "CalcCRC16": calcCrc
        }

    def validateSoftHeader(self, h, sh):
        if sh["CRC16"] != sh["CalcCRC16"]:
            raise Exception("Invalid Soft CRC16")
        if sh["ConstByte"] != 0x80:
            raise Exception("Invalid Const Soft Byte 0x80")
        if (h["From"] == self.conHardId and sh["From"] != self.conSoftId) or (
                h["From"] == self.devHardId and sh["From"] != self.devSoftId):
            raise Exception("Invalid From Address")
        if (h["To"] == self.conHardId and sh["To"] != self.conSoftId) or (
                h["To"] == self.devHardId and sh["To"] != self.devSoftId):
            raise Exception("Invalid To Address")

    def getTemp(self, w, divisor):
        w = self.getWord(w)
        if w & 0x8000:
            w = w - 0x10000
        return w / divisor

    def parseBitMask(self, val, ids, ret, regnum):
        ret[regnum] = [None] * len(ids)
        for idx in range(len(ids)):
            if ids[idx] is not None:
                ret[regnum][idx] = bool(val & 1)
            val = val >> 1

    def parseRegisters(self, m, regstart, reglen, unknown=False):
        ret = {}
        skip = 0
        for regnum in range(regstart, regstart + reglen, 2):
            if skip > 0:
                skip = skip - 1
                continue
            if regnum < self.REG_CONFIG_START:
                reg = self.StatusRegisters.get(regnum, None)
            else:
                reg = self.ConfigRegisters.get(regnum, None)
            adr = regnum - regstart
            if reg:
                val = None
                if reg['type'] == 'date':
                    val = "20{:02d}-{:02d}-{:02d}".format(m[adr], m[adr + 1], m[adr + 2])
                    skip = 1
                elif reg['type'] == 'time':
                    val = "{:02d}:{:02d}:{:02d}".format(m[adr], m[adr + 1], m[adr + 2])
                    skip = 1
                elif reg['type'] == 'word':
                    val = self.getWord(m[adr:])
                elif reg['type'] == 'rwrd':
                    val = self.getWordReverse(m[adr:])
                elif reg['type'] == 'dwrd':
                    val = self.getDWord(m[adr:])
                    skip = 1
                elif reg['type'] == 'temp':
                    val = self.getTemp(m[adr:], 1.0)
                elif reg['type'] == 'te10':
                    val = self.getTemp(m[adr:], 10.0)
                elif reg['type'] == 'fl10':
                    val = self.getWord(m[adr:]) / 10.0
                elif reg['type'] == 'f100':
                    val = self.getWord(m[adr:]) / 100.0
                elif reg['type'] == 'bool':
                    val = bool(self.getWord(m[adr:]))
                elif reg['type'] == 'mask':
                    self.parseBitMask(self.getWord(m[adr:]), reg['id'], ret, regnum)
                    continue
                elif reg['type'] == 'tprg':
                    raise Exception('tprg types not supported')
                    #skip = 1
                ret[regnum] = val
            elif unknown:
                ret["Reg%d" % regnum] = self.getWord(m[adr:])
        return ret

    def processMessage(self, m, ignoreTooShort):
        h = self.parseHardHeader(m)
        self.validateHardHeader(h)
        ml = h["Payload"]
        if ignoreTooShort and ml + 8 > len(m):
            return m
        sh = self.parseSoftHeader(h, m[8:ml + 8])
        self.validateSoftHeader(h, sh)
        self.updateHAStatus(h, sh, m)
        return m[ml + 8:]

    def updateHAStatus(self, h, sh, m):
        if sh["FNC"] == 0x50:
            mp = self.parseRegisters(sh["RestMessage"], sh["RegStart"], sh["RegLen"])
            for item in mp.items():
                if isinstance(item[1], dict):  # skipping dictionaries (time program)
                    continue
                if item[0] < self.REG_CONFIG_START:
                    reg = self.StatusRegisters.get(item[0], None)
                else:
                    reg = self.ConfigRegisters.get(item[0], None)
                if reg['ha_type'] == 'sensor':
                    reg['sensor'].set_state(item[1])
                    self.logger.info(reg['name']+' = '+str(item[1]))
                elif reg['ha_type'] == 'binarysensor':
                    if item[1] == 0:
                        reg['sensor'].off()
                        self.logger.info(reg['name'] + ' = off')
                    elif item[1] == 1:
                        reg['sensor'].on()
                        self.logger.info(reg['name'] + ' = on')
                elif reg['ha_type'] == 'binarysensors':
                    for idx in range (len(reg['id'])):
                        if item[1][idx] is not None:
                            if item[1][idx] == 0:
                                self.logger.info(reg['name'][idx] + ' = on')
                                reg['sensor'][idx].off()
                            if item[1][idx] == 1:
                                self.logger.info(reg['name'][idx] + ' = off')
                                reg['sensor'][idx].on()
                elif reg['ha_type'] == 'switch':
                    if item[1] == 0:
                        self.logger.info(reg['name']+ ' = off')
                        reg["switch"].off()
                    elif item[1] == 1:
                        self.logger.info(reg['name'] + ' = on')
                        reg["switch"].on()
                elif reg['ha_type'] == 'number':
                    self.logger.info(reg['name'] + ' = ' + str(item[1]))
                    reg['number'].set_value(item[1])
    def HACallbackSwitch(self,client: Client, reg, message: MQTTMessage):
        payload = message.payload.decode()
        self.logger.info(reg+': '+payload)
        self.ser = serial.serial_for_url("socket://%s:%s" % (self.PCWU_Address, self.PCWU_Port))
        self.ser.close()
        self.ser.open()
        if payload == "ON":
            self.write(self.ser, reg, 'True')
        elif payload == "OFF":
            self.write(self.ser, reg, 'False')
        else:
            self.logger.info("Unrecognized payload",payload)
        self.readConfigRegisters(self.ser)
        self.readStatusRegisters(self.ser)
        self.ser.close()

    def HACallbackNumber(self,client: Client, reg, message: MQTTMessage):
        payload = message.payload.decode()
        self.logger.info(reg+': '+payload)
        self.ser = serial.serial_for_url("socket://%s:%s" % (self.PCWU_Address, self.PCWU_Port))
        self.ser.close()
        self.ser.open()
        self.write(self.ser, reg, str(payload))
        self.readConfigRegisters(self.ser)
        self.readStatusRegisters(self.ser)
        self.ser.close()

    def processAllMessages(self, m, returnRemainingBytes=False):
        minLen = 8 if returnRemainingBytes else 0
        prevLen = len(m)
        while prevLen > minLen:
            m = self.processMessage(m, returnRemainingBytes)
            if len(m) == prevLen:
                if returnRemainingBytes:
                    return m
                else:
                    raise Exception("Something wrong")
            prevLen = len(m)
        return m

    def createReadRegistersMessage(self, start, num):
        header = [0x69, self.devHardId, self.conHardId, 0x84, 0, 0]
        payload = [(self.devSoftId & 0xff), ((self.devSoftId >> 8) & 0xff), (self.conSoftId & 0xff),
                   ((self.conSoftId >> 8) & 0xff), 0x40, 0x80, 0, num & 0xff, start & 0xff, (start >> 8) & 0xff]
        calcCrc16 = crc16(payload)
        payload.append((calcCrc16 >> 8) & 0xff)
        payload.append(calcCrc16 & 0xff)
        header.append(len(payload))
        calcCrc8 = crc8(header)
        header.append(calcCrc8)
        return bytearray(header + payload)

    def createWriteRegisterMessage(self, reg, val):
        header = [0x69, self.devHardId, self.conHardId, 0x84, 0, 0]
        payload = [(self.devSoftId & 0xff), ((self.devSoftId >> 8) & 0xff), (self.conSoftId & 0xff),
                   ((self.conSoftId >> 8) & 0xff), 0x60, 0x80, 0, 2, reg & 0xff, (reg >> 8) & 0xff, val & 0xff,
                   (val >> 8) & 0xff]
        calcCrc16 = crc16(payload)
        payload.append((calcCrc16 >> 8) & 0xff)
        payload.append(calcCrc16 & 0xff)
        header.append(len(payload))
        calcCrc8 = crc8(header)
        header.append(calcCrc8)
        return bytearray(header + payload)

    def readRegisters(self, ser, start, num):
        m = self.createReadRegistersMessage(start, num)
        ser.flushInput()
        ser.timeout = 0.4
        ser.write(m)
        r = ser.read(1000)
        return self.processAllMessages(r)

    def readStatusRegisters(self, ser):
        self.logger.info("--- Reading sensors")
        start = self.REG_STATUS_START
        return self.readRegisters(ser, start, self.REG_CONFIG_START - start)

    def readConfigRegisters(self, ser):
        self.logger.info("--- Reading configuration items")
        start = self.REG_CONFIG_START
        while start < self.REG_MAX_ADR:
            num = min(self.REG_MAX_ADR + 2 - start, self.REG_MAX_NUM)
            self.readRegisters(ser, start, num)
            start = start + num

    def writeRegister(self, ser, reg, val):
        m = self.createWriteRegisterMessage(reg, val)
        ser.flushInput()
        ser.timeout = 0.4
        ser.write(m)
        r = ser.read(1000)
        return self.processAllMessages(r)

    def write(self, ser, registerid, val):
        regnum = 0
        # look for register based on id
        for k, v in self.ConfigRegisters.items():
            if v['id'] == registerid:
                regnum = k
                break
        reg = self.ConfigRegisters.get(regnum, None)
        if reg:
            val = self.parseRegisterValue(reg, val)
            if val is not None:
                return self.writeRegister(ser, regnum, val)
        return None

    def parseRegisterValue(self, reg, val):
        if val:
            if reg['type'] == 'date':
                val = None
            elif reg['type'] == 'time':
                val = None
            elif reg['type'] == 'word':
                val = int(val)
            elif reg['type'] == 'rwrd':
                val = int(val)
            elif reg['type'] == 'dwrd':
                val = int(val)
            elif reg['type'] == 'temp':
                val = int(val)
            elif reg['type'] == 'te10':
                val = int(val) * 10
            elif reg['type'] == 'fl10':
                val = float(val) * 10
            elif reg['type'] == 'f100':
                val = float(val) * 100
            elif reg['type'] == 'bool':
                if val == 'True' or val == '1':
                    val = 1
                elif val == 'False' or val == '0':
                    val = 0
            elif reg['type'] == 'mask':
                val = None
            elif reg['type'] == 'tprg':
                val = None
            if reg['options'] and val not in reg['options']:
                print('invalid option ' + str(val))
                val = None
            return val

    # PCWU parameters
    #########################################
    # PCWU is driven by PG-426-P01 (controller) and MG-426-P01 (executive module)
    # Below are the registers for the executive module, so no controller settings
    # Registers are divided in read-only status registers and read/write config registers
    # The lowest readable register always seems to be 100
    REG_MIN_ADR = 100
    # The highest readable register varies per device
    REG_MAX_ADR = 536
    # The number of registers which can be read in one message varies per device
    REG_MAX_NUM = 226
    # Status registers start at 120 usually
    REG_STATUS_START = 120
    # Config registers start at a register which varies per device
    REG_CONFIG_START = 302

    StatusRegisters = {

        # Status registers
        #120: Date
        #124: Time
        128: {'type': 'te10', 'id': 'T_ambient', 'name':'Ambient Temperature', 'desc': 'T1 (Ambient temp)','ha_type':'sensor','unit':'°C'},
        130: {'type': 'te10', 'id': 'T_tank_bottom', 'name':'Tank Bottom Temperature','desc': 'T2 (Tank bottom temp)','ha_type':'sensor','unit':'°C'},
        132: {'type': 'te10', 'id': 'T_tank_top', 'name':'Tank Top Temperature','desc': 'T3 (Tank top temp)','ha_type':'sensor','unit':'°C'},
        138: {'type': 'te10', 'id': 'T_water_inlet', 'name':'Water Inlet Temperature','desc': 'T6 (HP water inlet temp)','ha_type':'sensor','unit':'°C'},
        140: {'type': 'te10', 'id': 'T_water_outlet', 'name':'Water Outlet Temperature','desc': 'T7 (HP water outlet temp)','ha_type':'sensor','unit':'°C'},
        142: {'type': 'te10', 'id': 'T_evap', 'name':'Evaporator Temperature', 'desc': 'T8 (HP evaporator temp)','ha_type':'sensor','unit':'°C'},
        144: {'type': 'te10', 'id': 'T_hp_before_comp', 'name':'HeatPump Temperature BefComp', 'desc': 'T9 (HP before compressor temp)','ha_type':'sensor','unit':'°C'},
        146: {'type': 'te10', 'id': 'T_hp_after_comp', 'name':'HeatPump Temperature AftComp', 'desc': 'T10 (HP after compressor temp)','ha_type':'sensor','unit':'°C'},
        194: {'type': 'bool', 'id': 'IsManual','name': 'Manual Mode','ha_type':'binarysensor'},
        196: {'type': 'mask',
              'id': ['FanON', None, 'CirculationPumpON', None, None, 'HeatPumpON', None, None, None, None, None, 'CompressorON', 'HeaterEON' ],
              'name': ['Fan', None, 'Circulation Pump', None, None, 'Heatpump', None, None, None, None, None, 'Compressor', 'Electric Heater' ],
              'sensor': ['Fan', None, None, None, None, None, None, None, None, None, None, None, None],
              'ha_type':'binarysensors'},
        198: {'type': 'word', 'id': 'EV1', 'name': 'Expansion valve','ha_type':'binarysensor'},
        #202: WaitingStatus
        #206: WaitingTimer
    }

    ConfigRegisters  = {
        # Config registers - Heat Pump
        #302: InstallationScheme -> word format not supported
        304: {'type': 'bool', 'id': 'HeatPumpEnabled', 'name':'Heat Pump','ha_type':'switch','options':[0,1]},
        # 306: TapWaterSensor -> word format not supported
        308: {'type': 'te10', 'id': 'TapWaterTemp', 'name': 'Tap Water Temperature Setpoint', 'options': range(100,600),'ha_type':'number'},
        310: {'type': 'te10', 'id': 'TapWaterHysteresis', 'name':'Tap Water Hysteresis','options': range(-20,100,10),'ha_type':'number'},
        312: {'type': 'te10', 'id': 'AmbientMinTemp', 'name':'Ambient Minimal Temperature', 'options': range(-100,100,10),'ha_type':'number'},
        # 314: TimeProgramHPM-F -> tprg format not supported
        # 318: TimeProgramHPSat -> tprg format not supported
        # 322: 'TimeProgramHPSun -> tprg format not supported
        326: {'type': 'bool', 'id': 'AntiFreezingEnabled','name':'Anti Freezing Enable','ha_type':'switch','options':[0,1]},
        # 328: 'WaterPumpOperationMode -> word format not supported
        # 330: 'FanOperationMode -> word format not supported
        # 332: DefrostingInterval -> word format not supported
        334: {'type': 'te10', 'id': 'DefrostingStartTemp','name':'Defrosting Start Temperature','ha_type':'number','options':range(-300,0,10)},
        336: {'type': 'te10', 'id': 'DefrostingStopTemp','name':'Defrosting Stop Temperature','ha_type':'number','options':range(20,300,10)},
        #338: 'DefrostingMaxTime' -> word format not supported
        #
        # Config registers - Heater E
        364: {'type': 'bool', 'id': 'HeaterEEnabled','name': 'Electric Heater Enabled','ha_type':'switch','options':[0,1]},
        366: {'type': 'te10', 'id': 'HeaterEHPONTemp','name':'Electric Heater Temperature HPON','ha_type':'number','options':range(300,600,10)},
        368: {'type': 'te10', 'id': 'HeaterEHPOFFTemp','name':'Electric Heater Temperature HPOFF','ha_type':'number','options':range(300,600,10)},
        370: {'type': 'bool', 'id': 'HeaterEBlocked','name':'Electric Heater Blocked','ha_type':'switch','options':[0,1]},
        # 374: HeaterETimeProgramM-F -> tprg format not supported
        # 378: HeaterETimeProgramSat -> tprg format not supported
        # 382: HeaterETimeProgramSun -> tprg format not supported
        #
        # Config registers - Anti-Legionella
        498: {'type': 'bool', 'id': 'AntiLegionellaEnabled','name': 'Anti Legionella Enabled','ha_type':'switch','options':[0,1]},
        500: {'type': 'bool', 'id': 'AntiLegionellaUseHeaterE','name': 'Anti Legionalle Use Electric Heater','ha_type':'switch','options':[0,1]},
        #502: 'AntiLegionellaUseHeaterP

        # Config registers - Ext Controller
        #516: ExtControllerHPOFF
        #518: ExtControllerHeaterEOFF
        #522: ExtControllerPumpFOFF
        #524: ExtControllerHeaterPOFF

    }