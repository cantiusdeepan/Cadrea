#######  File will publish a score between 0-5 on how good an idea
# (0- Don't open, 5 - Very good conditions for opening window)
# it is to open the window to clear the room given the current internal and external weather conditions
# Factors considered - ________
# Internal temperature
# External Temperature (Effect calculated by adaptive thermal comfort modelling formulation - ASHRAE standard)
# External Weather condition(smog,fog etc)
# External Relative Humidity
# External Wind speed/ Air velocity
# Current presence and Future presence prediction

import json
import time
import paho.mqtt.client as MQTT
import numpy as np
import random
import fpformat
import requests
import socket
from ThingspeakMqtt_Test import Thingspeak_MQTT

class MyMQTT:
    def __init__(self, broker, port, notifier):
        self.broker = broker
        self.port = port
        self.notifier = notifier
        self._paho_mqtt = MQTT.Client("Central_controller_main", False)
        self._paho_mqtt.on_connect = self.myOnConnect
        self._paho_mqtt.on_message = self.myOnMessageReceived

    def myOnConnect(self, paho_mqtt, userdata, flags, rc):
        pass

    def myOnMessageReceived(self, paho_mqtt, userdata, msg):
        self.notifier.notify(msg.topic, msg.payload)

    def myPublish(self, w, p, housIDvar):
        # print("barbastruzzo")
        js = {"data": "final_window", "value": w}
        topic = 'house/' + housIDvar + '/central_controller/final_window'
        self._paho_mqtt.publish(topic, json.dumps(js), 2)
        js = {"data": "final_purifier", "value": p}
        topic = 'house/' + housIDvar + '/central_controller/final_purifier'
        self._paho_mqtt.publish(topic, json.dumps(js), 2)

    # self._paho_mqtt.publish(topic, msg, qos)

    def mySubscribe(self, decision_temp_topic, decision_dust_topic, decision_gas_topic, decision_dust_window_topic,
                    decision_C_motion_topic, decision_P_motion_topic, internal_RH_topic, internal_temp_topic,
                    external_temperature, internal_dust, qos=2):
        self._paho_mqtt.subscribe(decision_temp_topic, qos)
        self._paho_mqtt.subscribe(decision_dust_topic, qos)
        self._paho_mqtt.subscribe(decision_gas_topic, qos)
        self._paho_mqtt.subscribe(decision_dust_window_topic, qos)
        self._paho_mqtt.subscribe(decision_C_motion_topic, qos)
        self._paho_mqtt.subscribe(decision_P_motion_topic, qos)

        self._paho_mqtt.subscribe(internal_RH_topic, qos)
        self._paho_mqtt.subscribe(internal_temp_topic, qos)
        self._paho_mqtt.subscribe(external_temperature, qos)
        self._paho_mqtt.subscribe(internal_dust, qos)

    def start(self):
        self._paho_mqtt.connect(self.broker, self.port)
        self._paho_mqtt.loop_start()

    def stop(self):
        self._paho_mqtt.loop_stop()


class StartCentralController():
    def __init__(self):
        #####Values to be fetched from local config
        # resource catalog base url
        self.rc_base_url = ""
        # Central config server base URL
        self.cc_base_url = ""
        self.house_id = 0
        self.mqtt_broker = ""
        self.mqtt_port = 0
        self.ChannelID_APIKEY = ""
        self.getLocalConfig()

        self.myMqtt = MyMQTT(self.mqtt_broker, self.mqtt_port, self)
        self.myMqtt.start()

        ##Decision make input variables
        self.decision_temp_topic_value = 0.0
        self.decision_dust_topic_value = 0.0
        self.decision_gas_topic_value = 0.0
        self.decision_dust_purifier_topic_value = 0.0
        self.decision_C_motion_topic_value = 0.0
        self.decision_P_motion_topic_value = 0.0
        self.presence_multiplier = 0

        ##Decision maker output variables
        self.final_window = 0
        self.final_purifier = 0

        ### Values only for publishing to thingspeak
        self.TS_MQTT = Thingspeak_MQTT()

        self.internal_RH_topic_value = 0.0
        self.internal_temp_topic_value = 0.0
        self.external_temperature_value = 0.0
        self.internal_dust_value = 0.0
        self.external_dust_value = 0.0

        self.central_controller()

    def getLocalConfig(self):
        json_file = open('local_centre_config.json').read()
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

        self.ChannelID_APIKEY = self.getIDfromRC(self.rc_base_url, 'getTSCID4HID:', self.house_id)

    def updateThingSpeak(self):
        print("Inside Thingspeak Publisher")

        # Send following values to Thingspeak
        # int_temp, int_RH, ext_temp, int_dust, ext_dust, presence, purifier_status, window_status

        returnState = self.TS_MQTT.mqttConnection(self.ChannelID_APIKEY, self.internal_temp_topic_value,
                                                  self.internal_RH_topic_value,
                                                  self.external_temperature_value, self.internal_dust_value,
                                                  self.decision_gas_topic_value
                                                  , self.presence_multiplier, self.final_purifier, self.final_window)

    # Common method to get values from RC based on a command and the param for the command
    def getIDfromRC(self, url, command, param):

        # Sent : address of the raspberry pi or house ID  et.c
        # Received:  House iD or Sensor list etcto

        data = command + param
        print data
        try:
            response = requests.post(url, data=data)
            print response.text

            return response.text
        except:
            print("Error in fetching data from resource catalog:", data)
            pass

    def end(self):
        self.myMqtt.stop()

    def central_controller(self):

        # house_id = self.getIDfromRC(rc_base_url,'getHID4pi:',local_ip_addr)
        ###Values required for decision making
        decision_temp_topic = 'house/' + str(self.house_id) + '/temp_local_controller/temp_window'
        decision_dust_topic = 'house/' + str(self.house_id) + '/dust_local_controller/dust_window'
        decision_gas_topic = 'house/' + str(self.house_id) + '/gas_local_controller/gas_window'
        decision_dust_window_topic = 'house/' + str(self.house_id) + '/dust_local_controller/purifier'
        decision_C_motion_topic = 'house/' + str(self.house_id) + '/motion_local_controller/motion_status'
        decision_P_motion_topic = 'house/' + str(self.house_id) + '/prediction_local_controller/predict_motion'

        ##Values only for TS comms - not used in decsion making

        internal_temp_topic = 'house/' + str(self.house_id) + '/sensor/temp/internal'
        internal_RH_topic = 'house/' + str(self.house_id) + '/sensor/rhumidity/internal'
        external_temperature = '/wunderground/temp/Turin'
        internal_dust = 'house/' + str(self.house_id) + '/sensor/dust/internal'
        # external_dust = 'house/' + str(self.house_id) + '/sensor/dust/external'



        self.myMqtt.mySubscribe(decision_temp_topic, decision_dust_topic, decision_gas_topic,
                                decision_dust_window_topic,
                                decision_C_motion_topic, decision_P_motion_topic, internal_RH_topic, internal_temp_topic,
                                external_temperature, internal_dust, 2)

        while True:
            time.sleep(30)
            print"_____________________________________________________________________________"
            print"decision_temp_topic_value:", self.decision_temp_topic_value
            print"decision_dust_topic_value:", self.decision_dust_topic_value
            print"decision_gas_topic_value:", self.decision_gas_topic_value
            print"decision_dust_purifier_topic_value:", self.decision_dust_purifier_topic_value
            print"decision_C_motion_topic_value:", self.decision_C_motion_topic_value
            print"decision_P_motion_topic_value:", self.decision_P_motion_topic_value

            weighted_window_value = self.decision_temp_topic_value * (2 * self.decision_dust_topic_value)
            self.presence_multiplier = 0

            if (self.decision_gas_topic_value > 0):
                print("High Alert!!!! - Gas leak detected")
                self.final_window = 1
                self.final_purifier = 1
            else:
                if (self.decision_dust_purifier_topic_value <= 0):
                    print("No cleaning required")
                    self.final_window = 0
                    self.final_purifier = 0
                elif (weighted_window_value >= 10):
                    print("weighted window value suggests opening window is a good idea")
                    self.final_window = 1
                    self.final_purifier = 0
                else:
                    print("Conditions not good for opening window- Run purifier")
                    self.final_window = 0
                    self.final_purifier = 1
                if (self.decision_C_motion_topic_value == 1):
                    print("presence detected-hold decision made previously")
                    self.presence_multiplier = 1
                elif (self.decision_C_motion_topic_value == 0):
                    print("Presence NOT detected-Check presence predcition")

                    if (self.decision_P_motion_topic_value == 1):
                        print("Presence not detected now- but predicted for near future")
                        self.presence_multiplier = 1
                    elif (self.decision_C_motion_topic_value == 0):
                        print("Presence not detected now- and also not predicted for near future")
                        self.presence_multiplier = 0
                    else:
                        print("Possible problem in prediction-Hold previous presence multiplier")
                        pass


                else:
                    print("Possible problem in presence detection-Hold previous presence multiplier")
                    pass

                self.final_window = self.final_window * self.presence_multiplier
                self.final_purifier = self.final_purifier * self.presence_multiplier

            self.myMqtt.myPublish(self.final_window, self.final_purifier, self.house_id)
            print("*****************************************************************")
            print "FINAL window: " + str(self.final_window)
            print "FINAL purifier: " + str(self.final_purifier)
            print("*****************************************************************")

            self.updateThingSpeak()

    def notify(self, topic, msg):
        topicName = topic

        ####Values for decision making
        if "/temp_local_controller/temp_window" in topic:
            topicName = "Temp_decision_window"
            self.decision_temp_topic_value = float((json.loads(msg)['value']))

        if "/dust_local_controller/dust_window" in topic:
            topicName = "Dust_decision_window"
            self.decision_dust_topic_value = float((json.loads(msg)['value']))

        if "/gas_local_controller/gas_window" in topic:
            topicName = "Gas_decision_Window"
            self.decision_gas_topic_value = float((json.loads(msg)['value']))

        if "/dust_local_controller/purifier" in topic:
            topicName = "Dust_decision_Purifier"
            self.decision_dust_purifier_topic_value = float((json.loads(msg)['value']))

        if "/motion_local_controller/motion_status" in topic:
            topicName = "Motion_Status"
            self.decision_C_motion_topic_value = float((json.loads(msg)['value']))

        if "/prediction_local_controller/predict_motion" in topic:
            topicName = "Motion_Prediction"
            self.decision_P_motion_topic_value = float((json.loads(msg)['value']))

        ####Values for TS publish only
        if topic == "/wunderground/temp/Turin":
            topicName = "Outside Temp"
            self.external_temperature_value = (json.loads(msg)['value'])
        if "/sensor/temp/internal" in topic:
            topicName = "Internal Temp"
            internal_temp_temporary = (json.loads(msg)['value'])
            if (internal_temp_temporary != "-100"):
                self.internal_temp_topic_value = internal_temp_temporary
                # checking if we have value from sensor, if not skip and use default value
            else:
                self.internal_temp_topic_value = 0.0
        if "/sensor/rhumidity/internal" in topic:
            topicName = "Internal RHumidity"
            internal_rhumidity_temporary = (json.loads(msg)['value'])
            # checking if we have value from sensor, if not skip and use default value
            if (internal_rhumidity_temporary != "-1"):
                self.internal_RH_topic_value = internal_rhumidity_temporary
            else:
                self.internal_RH_topic_value = 0.0
        if "/sensor/dust/internal" in topic:
            topicName = "Internal Dust"
            self.internal_dust_value = (json.loads(msg)['value'])

        if "/sensor/dust/external" in topic:
            topicName = "External Dust"
            self.external_dust_value = (json.loads(msg)['value'])

        print " MQTT Received  under topic:%s  -- %s" % (topicName, (json.loads(msg)['value']))


if __name__ == "__main__":
    C = StartCentralController()
    # time.sleep(30)
    # test.end()
