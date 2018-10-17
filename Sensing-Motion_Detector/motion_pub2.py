#This code runs on the Raspberry Pi
#Connection to the motion sensor, processing the motion data and publishing on MQTT every time instant (ex.30 seconds)

import time
import json
import Adafruit_DHT
from gpiozero import MotionSensor
import paho.mqtt.client as MQTT
import random
import sys
import os
import urllib2
import numpy
from datetime import datetime

motion_dic = {"motion": []}
detection = 0
counter = 0
presence_avg = 0

class MotionPub:
    def __init__(self):
        print "hello"
        self.house_id = ""
        self.mqtt_broker = ""
        self.mqtt_port = 0
        self.RC_config_reader()
        self._pahoMotion=MQTT.Client("Motion_pub",False)
        self._pahoMotion.on_connect= self.myOnConnect
        print "MQTT broker %s and MQTT port %s" % (self.mqtt_broker, str(self.mqtt_port))
        self._pahoMotion.connect(self.mqtt_broker,self.mqtt_port)

        self.getMotionData()


#We get a Motion value every X seconds, we wait for Y values and then we process them
# we do the average of all values and we decide whether there was motion or not
# the threshold for this decision depends on the sensor accuracy and its importance for the actuation
# for our purpose, we get a Motion value every 3 seconds, we wait for 10 values to process and the threshold is set to 0.05
# every 3*10 = 30 seconds we publish the decided motion value on MQTT

    def getMotionData(self):

        global detection
        global counter
        global presence_avg

        pir = MotionSensor(4)

        print "Publishing every 3*10 = 30 seconds"

        while True:

            counter = counter+1
            print "Counter: ", counter
            #print "I'm sleeping for 30 secs.."
            time.sleep(3)

            if pir.motion_detected:
                motion_dic["motion"].append(1)
            else:
                motion_dic["motion"].append(0)
            if (counter == 10):
                print "Motion dic: ", motion_dic
                presence_avg = numpy.mean(motion_dic["motion"])
                print "Presence_avg is: ", presence_avg

                if (float(presence_avg) > 0.05):
                    print "There was presence."
                    detection = 1
                else:
                    print "There was NO presence."
                    detection = 0

                print "I'm publishing %d for house id %s" % (int(detection), self.house_id)
                self.myPublish(int(detection),self.house_id)
                detection = 0
                counter = 0
                del motion_dic["motion"][:]


#With this method we publish the motion status

    def myPublish(self,det,hid):
        self._pahoMotion.loop_start()
        js={"data":"motion","value": det}
        motion_topic = 'house/'+hid+'/motion_local_controller/motion_status'
        self._pahoMotion.publish(motion_topic,json.dumps(js), 2)

    def myOnConnect(self, paho_mqtt, userdata, flags, rc):
        print ("Connected to message broker with result code: " + str(rc))

#With this method we are reading necessary data from the motion_config.json file

    def RC_config_reader(self):

        json_file = open('motion_config.json').read()
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
            print "MQTT broker %s " % (self.mqtt_broker)
        else:
            print "Problem in local json - Can't get mqtt_broker"
        if local_config.get("mqtt_port"):
            self.mqtt_port = local_config["mqtt_port"]
        else:
            print "Problem in local json - Can't get mqtt_port"


if __name__ == '__main__':
    ws=MotionPub()



