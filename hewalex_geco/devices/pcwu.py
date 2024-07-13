from .base import BaseDevice

# Based on work by krzysztof1111111111
# https://www.elektroda.pl/rtvforum/topic3499254.html


class PCWU(BaseDevice):

    # PCWU is driven by PG-426-P01 (controller) and MG-426-P01 (executive module)
    # Below are the registers for the executive module, so no controller settings
    REG_MAX_ADR = 536
    REG_MAX_NUM = 226
    REG_CONFIG_START = 302

    # Interaction between status register 202 and config register 304:
    #
    # When talking to the executive module directly the heat pump can be (manually)
    # disabled and enabled through config register 304 and the result of this is visible
    # in status register 202. With the controller on this works as expected, the heat
    # pump can be put into a waiting mode where it will not turn on until enabled again
    # through register 304. With the controller off however this doesn't work. Maybe
    # the executive module is hardcoded to not turn the heat pump on when the controller
    # is off? See eavesDrop function in base device to learn how the executive module
    # knows that the controller is off. What makes this especially weird is that register
    # 202 changes its value to 0 when the controller is off even if register 304 says
    # otherwise. It would be great if we could detect the 'controller is off' situation
    # through one of the registers, but I haven't found a way yet.

    registers = {

        # Status registers
        120: { 'type': 'date', 'name': 'date', 'desc': 'Date' },                      
        124: { 'type': 'time', 'name': 'time', 'desc': 'Time' },                     
        128: { 'type': 'te10', 'name': 'T1', 'desc': 'T1 (Ambient temp)' },                        
        130: { 'type': 'te10', 'name': 'T2', 'desc': 'T2 (Tank bottom temp)' },                         
        132: { 'type': 'te10', 'name': 'T3', 'desc': 'T3 (Tank top temp)' },                        
        138: { 'type': 'te10', 'name': 'T6', 'desc': 'T6 (HP water inlet temp)' },                         
        140: { 'type': 'te10', 'name': 'T7', 'desc': 'T7 (HP water outlet temp)' },                         
        142: { 'type': 'te10', 'name': 'T8', 'desc': 'T8 (HP evaporator temp)' },                          
        144: { 'type': 'te10', 'name': 'T9', 'desc': 'T9 (HP before compressor temp)' },                          
        146: { 'type': 'te10', 'name': 'T10', 'desc': 'T10 (HP after compressor temp)' },                         

        194: { 'type': 'bool', 'name': 'IsManual' },
        196: { 'type': 'mask', 'name': [
            'FanON',                                                    # Fan ON (True/False)
            None,
            'CirculationPumpON',                                        # Circulation pump ON (True/False)
            None,
            None,
            'HeatPumpON',                                               # Heat pump ON (True/False)
            None,
            None,
            None,
            None,
            None,
            'CompressorON',                                             # Compressor ON (True/False)
            'HeaterEON',                                                # Heater E ON (True/False)
        ]},
        198: { 'type': 'word', 'name': 'EV1', 'desc': 'Expansion valve' },
        202: { 'type': 'word', 'name': 'WaitingStatus', 'desc': ' 0 when available for operation, 2 when disabled through register 304' },               #
        206: { 'type': 'word', 'name': 'WaitingTimer', 'desc': 'Timer counting down to 0 when just stopped and waiting to be available for operation again' },

        # Config registers - Heat Pump
        302: { 'type': 'word', 'name': 'InstallationScheme', 'options': [1,2,3,4,5,6,7,8,9], 'desc': 'Installation Scheme (1-9)' },
        304: { 'type': 'bool', 'name': 'HeatPumpEnabled', 'options': [0,1], 'desc': 'Heat Pump Enabled (True/False)'},
        306: { 'type': 'word', 'name': 'TapWaterSensor', 'options': [0,1,2], 'desc': 'Temp. sensor controlling heat pump operation [T2,T3,T7, factory setting T2]' },                                  #
        308: { 'type': 'te10', 'name': 'TapWaterTemp', 'options':  [100,110,112,130,140,150,160,170,180,190,    #
                                                                    200,210,220,230,240,250,260,270,280,290,
                                                                    300,310,320,330,340,350,360,370,380,390,
                                                                    400,410,420,430,440,450,460,470,480,490,
                                                                    500,510,520,530,540,550,560,570,580,590,
                                                                    600] , 'desc': 'HUW temperature for heat pump [10-60°C, factory setting 50°C]'},                                 
        310: { 'type': 'te10', 'name': 'TapWaterHysteresis', 'options': [20,30,40,50,60,70,80,90,100] , 'desc': 'Heat pump start-up hysteresis [2-10°C, factory setting 5°C]'},        # 
        312: { 'type': 'te10', 'name': 'AmbientMinTemp', 'options': [-100,-90,-80,-70,-60,-50,-40,-30,-20,-10,  # 
                                                                     10,20,30,40,50,60,70,80,90,100] , 'desc': 'Minimum ambient temperature (T1) [-10-10°C] ' },                                                
        314: { 'type': 'tprg', 'name': 'TimeProgramHPM-F', 'desc': 'Time Program HP M-F (True/False per hour of the day)' },                                                    # 
        318: { 'type': 'tprg', 'name': 'TimeProgramHPSat', 'desc': 'Time Program HP Sat (True/False per hour of the day)' },                                                    # 
        322: { 'type': 'tprg', 'name': 'TimeProgramHPSun', 'desc': 'Time Program HP Sun (True/False per hour of the day)' },                                                    # 

        326: { 'type': 'bool', 'name': 'AntiFreezingEnabled', 'options': [0,1], 'desc': 'Function protecting against freezing [YES/NO], factory setting YES' },                               # 
        328: { 'type': 'word', 'name': 'WaterPumpOperationMode', 'options': [0,1], 'desc': 'Water Pump Operation Mode (0=Continuous, 1=Synchronous)' },                            # 
        330: { 'type': 'word', 'name': 'FanOperationMode', 'options': [0,1,2], 'desc': 'Fan Operation Mode (0=Max, 1=Min, 2=Day/Night), factory MAX' },                                # 
        332: { 'type': 'word', 'name': 'DefrostingInterval', 'desc': 'Defrosting cycle start-up delay [30-90 min., factory setting 45 min.]' },                                                  # 
        334: { 'type': 'te10', 'name': 'DefrostingStartTemp', 'desc': 'Temperature activating defrosting [-30 - 0°C, factory setting -7°C]' },                                                 # 
        336: { 'type': 'te10', 'name': 'DefrostingStopTemp', 'desc': 'Temperature finishing defrosting [2-30°C, factory setting 13°C]' }, 
        338: { 'type': 'word', 'name': 'DefrostingMaxTime', 'desc': 'Maximum defrosting duration [1-12 min., factory setting 8 min.]' },

        # Config registers - Heater E
        364: { 'type': 'bool', 'name': 'HeaterEEnabled', 'options': [0,1], 'desc': 'Heater E Enabled (True/False)' },
        366: { 'type': 'te10', 'name': 'HeaterEHPONTemp', 'options':  [100,110,112,130,140,150,160,170,180,190,    #
                                                                    200,210,220,230,240,250,260,270,280,290,
                                                                    300,310,320,330,340,350,360,370,380,390,
                                                                    400,410,420,430,440,450,460,470,480,490,
                                                                    500,510,520,530,540,550,560,570,580,590,
                                                                    600] , 'desc': 'Heater E water temp when HP ON (45.0)' },
        368: { 'type': 'te10', 'name': 'HeaterEHPOFFTemp', 'options':  [100,110,112,130,140,150,160,170,180,190,    #
                                                                    200,210,220,230,240,250,260,270,280,290,
                                                                    300,310,320,330,340,350,360,370,380,390,
                                                                    400,410,420,430,440,450,460,470,480,490,
                                                                    500,510,520,530,540,550,560,570,580,590,
                                                                    600] , 'desc': 'Heater E water temp when HP OFF (55.0)' },
        370: { 'type': 'bool', 'name': 'HeaterEBlocked', 'options': [0,1], 'desc': 'Heater E blocked when HP ON? (True/False)' },
        374: { 'type': 'tprg', 'name': 'HeaterETimeProgramM-F', 'desc': 'Heater E Time Program M-F (True/False per hour of the day)' },
        378: { 'type': 'tprg', 'name': 'HeaterETimeProgramSat', 'desc': 'Heater E Time Program Sat (True/False per hour of the day)' },
        382: { 'type': 'tprg', 'name': 'HeaterETimeProgramSun', 'desc': 'Heater E Time Program Sun (True/False per hour of the day)' },

        # Config registers - Anti-Legionella
        498: { 'type': 'bool', 'name': 'AntiLegionellaEnabled', 'options': [0,1], 'desc': 'Anti-Legionella Enabled (True/False)' },
        500: { 'type': 'bool', 'name': 'AntiLegionellaUseHeaterE', 'options': [0,1], 'desc': 'Anti-Legionella Use Heater E (True/False)' },
        502: { 'type': 'bool', 'name': 'AntiLegionellaUseHeaterP', 'options': [0,1], 'desc': 'Anti-Legionella Use Heater P (True/False)' },
        
        # Config registers - Ext Controller
        516: { 'type': 'bool', 'name': 'ExtControllerHPOFF', 'options': [0,1], 'desc': 'Ext Controller HP OFF (True/False)' },
        518: { 'type': 'bool', 'name': 'ExtControllerHeaterEOFF', 'options': [0,1], 'desc': 'Ext Controller Heater E OFF (True/False)' },
        522: { 'type': 'bool', 'name': 'ExtControllerPumpFOFF', 'options': [0,1], 'desc': 'Ext Controller Pump F OFF (True/False)' },
        524: { 'type': 'bool', 'name': 'ExtControllerHeaterPOFF', 'options': [0,1], 'desc': 'Ext Controller Heater P OFF (True/False)' },      

    }

    def disable(self, ser):
        return self.writeRegister(ser, 304, 0)

    def enable(self, ser):
        return self.writeRegister(ser, 304, 1)



            

                    
