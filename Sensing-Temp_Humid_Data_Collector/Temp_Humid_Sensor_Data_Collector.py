# Import all the libraries we need to run
import sys
# import RPi.GPIO as GPIO
import socket
import os
from time import sleep
import Adafruit_DHT
import paho.mqtt.client as MQTT
import urllib2
import random
# from ThingspeakMqtt_Test import HouseMqttUpdating
import json
import requests


class MyMQTT:
    def __init__(self, broker, port, notifier):
        self.broker = broker
        self.port = port
        self.notifier = notifier
        self._paho_mqtt = MQTT.Client("Int_Temp_Humid_reader", False)
        self._paho_mqtt.on_connect = self.myOnConnect
        self._paho_mqtt.on_message = self.myOnMessageReceived

    def myOnConnect(self, paho_mqtt, userdata, flags, rc):
        print ("Connected to message broker with result code: " + str(rc))

    def myOnMessageReceived(self, paho_mqtt, userdata, msg):
        self.notifier.notify(msg.topic, msg.payload)

    def myPublish(self, T, H, house_id):
        # print("barbastruzzo")
        internal_temp_topic = 'house/' + house_id + '/sensor/temp/internal'
        internal_RH_topic = 'house/' + house_id + '/sensor/rhumidity/internal'

        js = {"data": "internal_temp", "value": T}
        self._paho_mqtt.publish(internal_temp_topic, json.dumps(js), 2)
        js = {"data": "internal_RH", "value": H}
        self._paho_mqtt.publish(internal_RH_topic, json.dumps(js), 2)

    # self._paho_mqtt.publish(topic, msg, qos)

    def mySubscribe(self, topicSub, qos=2):
        self._paho_mqtt.subscribe(topicSub, qos)

    def start(self):
        self._paho_mqtt.connect(self.broker, self.port)
        self._paho_mqtt.loop_start()

    def stop(self):
        self._paho_mqtt.loop_stop()


class HouseMain:
    def __init__(self):
        self.data = {"temp": [], "humid": []}
        #####Values to be fetched from local config
        # resource catalog base url
        self.rc_base_url = ""
        # Central config server base URL
        self.cc_base_url = ""
        self.house_id = 0
        self.mqtt_broker = ""
        self.mqtt_port = 0
        self.getLocalConfig()

        self.myMqtt = MyMQTT(self.mqtt_broker, self.mqtt_port, self)
        self.myMqtt.start()

    def getLocalConfig(self):
        json_file = open('local_TH_config.json').read()
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

    def get_pi_local_ip_address(self, target):
        ipaddr = ''
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect((target, 8000))
            ipaddr = s.getsockname()[0]
            print ipaddr
            s.close()
        except:
            pass

        return ipaddr

    # Common method to get values from RC based on a command and the param for the command
    def getIDfromRC(self, url, command, param):

        # Sent : address of the raspberry pi or house ID  et.c
        # Received:  House iD or Sensor list etcto

        data = command + param
        print data
        try:
            response = requests.post(url, data=data)

            return response.text
        except:
            print("Error in fetching data from resource catalog:", data)
            pass

    def getSensorData(self):

        humidity, temperature = Adafruit_DHT.read_retry(11, 2)  # 11 stands for DHT11 and 2 for pin to read

        return (str(temperature), str(humidity))

    def enterSleepMode(self, rc_base_url, house_id):
        # Sleep for one hour and then check if  we can get out of vacation mode
        sleep(300)

        program_status = 0

        while True:
            sensorList = self.getIDfromRC(rc_base_url, 'getSensorList4HID:', house_id)
            json_file = open('local_TH_config.json').read()
            local_config = json.loads(json_file)
            ### Getting and storing data from local config
            # program status :: 1 - active, 0-sleep mode/vacation mode

            if local_config.get("Active_Status"):
                program_status = local_config["Active_Status"]
            else:
                print "Problem in local json - Can't get RC url"
            if ("TH" in sensorList and program_status > 0):
                print "program status changed,exiting sleep mode"

                return (True)
            else:
                print "Still in sleep mode- continue sleep for five mins, then check again"

    # main() function
    def gethouseControlMain(self, myDelay):

        print 'starting...'
        # program status :: 1 - active, 0-sleep mode/vacation mode
        program_status = 0
        while True:
            try:
                sensorList = self.getIDfromRC(self.rc_base_url, 'getSensorList4HID:', self.house_id)
                print ("SensorList:", sensorList)
                json_file = open('local_TH_config.json').read()
                local_TH_config = json.loads(json_file)

                if local_TH_config.get("Active_Status"):
                    program_status = local_TH_config["Active_Status"]

                if ("TH" in sensorList and program_status > 0):
                    T, H = self.getSensorData()
                else:
                    print "Entering sleepmode as either sensor not available in house or vacation mode started"
                    T = -100
                    H = -1
                    self.myMqtt.myPublish(T, H, self.house_id)
                    self.enterSleepmode(self.rc_base_url, self.house_id)
                    # print "No temp and Humid data in the house, so sending -1"

                # Keep only 30 days worth of temperature and humidity data
                # 12 readings per hour for 24 h = 288 readings per day
                # 288 readings per day for 30 days = 8640
                try:
                    if (str(self.data["temp"]).count(",") > 8640):
                        self.data["temp"].pop(0)

                    if (str(self.data["humid"]).count(",") > 8640):
                        self.data["humid"].pop(0)
                except:
                    print "Some error in checking size of TempHumid.json - skipping ahead for now"
                    pass
                self.data["temp"].append(T)
                self.data["humid"].append(H)
                print "Temp and Humid sensor data received"
                print "Temperature:", T + "\nHumidity: ", H

                # Fill in the txt files with info from sensors
                # For reference and future improvements to include prediction algorithm
                temp_file = open("TempHumid.json", "w")

                json.dump(self.data, temp_file)
                temp_file.close()

                # Pubish Internal T & H data on local MQTT broker
                self.myMqtt.myPublish(T, H, self.house_id)
                print "Back to loop"

                sleep(int(myDelay))
            except IOError as e:
                print "I/O error({0}): {1}".format(e.errno, e.strerror)
                sys.exit(1)
            except ValueError:
                print "Could not convert ."
                sys.exit(1)

            except:
                print "Exiting.....due to unknown exception", sys.exc_info()[0]
                sys.exit(1)


# call main
if __name__ == '__main__':
    hClass = HouseMain()
    hClass.gethouseControlMain(30)  # Setting delay between consecutive sensor readings for T&H
