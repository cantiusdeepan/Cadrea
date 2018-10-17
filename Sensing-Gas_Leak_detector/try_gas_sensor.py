import json
import paho.mqtt.client as MQTT
import time , sys
import random
import RPi.GPIO as GPIO
import requests
import socket

class gasPubblisher:
    def action(self, pin):
        self.gas_value = self.gas_value+1
        #self.pubblishing_value=1
        # gas1 = {"mesurement": "gas", "value": 1}
        # self._pahoPG.publish('/sensor/analog/gas', json.dumps(gas1), 2)
        print("gas alarm!")
        # time.sleep(30)

    def __init__(self):
        self.gas_value = 0
        self.checking_value=0
        self.pubblishing_value=0
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(26, GPIO.RISING)
        GPIO.add_event_callback(26, self.action)
        self.rc_base_url=""
        self.cc_base_url=""
        self.house_id=""
        self.mqtt_broker=""
        self.mqtt_port=""
        self.ChannelID_APIKEY=""
        self.getLocalConfig()
        self._pahoPG=MQTT.Client("gas_sensor",False)
        self._pahoPG.on_connect = self.myOnConnect
        self._pahoPG.connect(self.mqtt_broker, self.mqtt_port)
        self._pahoPG.loop_start()
        while True:
            self.gas_method()
            self.checking_method()
            self.mypubblish()
            time.sleep(15)

    def gas_method(self):
        if self.gas_value%2!=0:
            self.checking_value+=1
        else:
            self.checking_value=0
        #self.gas_value=0

    def checking_method(self):
        if self.checking_value>1:
            self.pubblishing_value=1
        else:
            self.pubblishing_value=0

    def getLocalConfig(self):
        json_file = open('Gas_sensor_config.json').read()
        local_config = json.loads(json_file)

        if local_config.get("RC_base_url"):
            self.rc_base_url = local_config["RC_base_url"]
        else:
            print "Problem in local json - Can't get RC url"
        if local_config.get("Central_config_base_url"):
            self.cc_base_url = local_config["Central_config_base_url"]
        else:
            print "Problem in local json - Can't get Central config url"
        if local_config.get("house_id"):
            self.house_id = local_config["house_id"]
        else:
            print "Problem in local json - Can't get house_id"
        if local_config.get("mqtt_broker"):
            self.mqtt_broker = local_config["mqtt_broker"]
        else:
            print "Problem in local json - Can't get mqtt_broker"
        if local_config.get("mqtt_port"):
            self.mqtt_port = local_config["mqtt_port"]
        else:
            print "Problem in local json - Can't get mqtt_port"

         #   self.ChannelID_APIKEY = self.getIDfromRC(self.rc_base_url, 'getTSCID4HID:', self.house_id)

    def mypubblish(self):
        gas1 = {"mesurement": "gas", "value": int(self.pubblishing_value)}
        self._pahoPG.publish('house/'+str(self.house_id)+'/gas_local_controller/gas_window', json.dumps(gas1), 2)
        print("hei, gas: "+str(self.pubblishing_value))
        #self.gas_value = 0




   # def getGas(self):
        # in_gas = 0
        #gas_value=random.randint(0,85)
        #in_gas = raw_input("Insert indoor gas value: ")
    #    gas1={"mesurement": "gas","value":0}
   #     self._pahoPG.publish('/sensor/analog/gas', json.dumps(gas1), 2)
        #print int("no gas")

    def myOnConnect(self, paho_mqtt, userdata, flags, rc):
        print ("Connected to message broker with result code: " + str(rc))

   # def connection(self):
    #    self.getGas()

if __name__ == '__main__':
    gp=gasPubblisher()