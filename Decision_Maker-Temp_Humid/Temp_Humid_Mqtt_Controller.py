#######  File will publish a score between 0-5 on how good an idea
# (0- Don't open, 5 - Very good conditions for opening window)
# it is to open the window to clear the room given the current internal and external weather conditions
# Factors considered - ________
# Internal temperature
# External Temperature (Effect calculated by adaptive modelling formulation - ASHRAE standard)
# External Weather condition(smog,fog etc)
# External Relative Humidity
# External Wind speed/ Air velocity



import json
import time
import paho.mqtt.client as MQTT
import numpy as np
import random
import fpformat
import requests
import socket


class MyMQTT:
    def __init__(self, broker, port, notifier):
        self.broker = broker
        self.port = port
        self.notifier = notifier
        self._paho_mqtt = MQTT.Client("Temp_Humid_Decision_Maker", False)
        self._paho_mqtt.on_connect = self.myOnConnect
        self._paho_mqtt.on_message = self.myOnMessageReceived

    def myOnConnect(self, paho_mqtt, userdata, flags, rc):
        # print ("Connected to message broker with result code: " + str(rc))
        pass

    def myOnMessageReceived(self, paho_mqtt, userdata, msg):
        self.notifier.notify(msg.topic, msg.payload)

    def myPublish(self, housIDvar, w):
        # print("barbastruzzo")
        js_pub = {"data": "temp_window", "value": w}
        topic_pub = 'house/' + housIDvar + '/temp_local_controller/temp_window'
        self._paho_mqtt.publish(topic_pub, json.dumps(js_pub), 2)
        print("Publishing TempHumid decision on MQTT")

    # self._paho_mqtt.publish(topic, msg, qos)

    def mySubscribe(self, topicExtTemp, topicExtWind, topicExtWeather, topicExtRH, topicIntTemp, topicIntRH, qos=2):
        self._paho_mqtt.subscribe(topicExtTemp, qos)
        self._paho_mqtt.subscribe(topicExtWind, qos)
        self._paho_mqtt.subscribe(topicExtWeather, qos)
        self._paho_mqtt.subscribe(topicExtRH, qos)
        self._paho_mqtt.subscribe(topicIntTemp, qos)
        self._paho_mqtt.subscribe(topicIntRH, qos)

    def start(self):
        self._paho_mqtt.connect(self.broker, self.port)
        self._paho_mqtt.loop_start()

    def stop(self):
        self._paho_mqtt.loop_stop()


class StartTempHumidMqtt():
    def __init__(self):
        #####Values to be fetched from local config
        # resource catalog base url
        self.rc_base_url = ""
        # Central config server base URL
        self.cc_base_url = ""
        self.house_id = 0
        self.mqtt_broker = ""
        self.mqtt_port = 0
        self.getLocalConfig()
        self.runningMonthMeanOutTemp = 0.0

        ## Values to be used in the logical decision making section
        # setting default initial values
        self.internal_temp = 0.0
        self.external_temp = 20.0
        self.external_wind = 0.0
        self.external_weather = 0
        self.l_threshold_temp = 15.0
        self.u_threshold_temp = 30.0
        self.external_rHumidity = 45.0
        self.window = 0.0

        self.internal_rhumidity = 45.0
        self.last_month_ext_temp_list = np.array([])

        self.myMqtt = MyMQTT(self.mqtt_broker, self.mqtt_port, self)
        self.myMqtt.start()

    def getLocalConfig(self):
        json_file = open('local_TH_control_config.json').read()
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

    def thresholdValuesFromCentre(self, url, house_ID, reqString='index.html'):
        # URL of the GUIWebservice for Central config file
        # url = 'http://192.168.1.71:8081/'

        updated_url = url + house_ID + "/" + reqString
        print "updated_url:", updated_url
        try:
            response = requests.get(updated_url)
            print response.text

            return str(response.text)
        except:
            print("Error in fetching thingspeak ID from resource catalog")
            pass

    # Getting thingspeak ID from RC using rasp pi IP

    def running_mean(self, current_ext_temp, array_size_limit):

        self.last_month_ext_temp_list = np.append(self.last_month_ext_temp_list, current_ext_temp)

        self.ext_temp_array_size = self.last_month_ext_temp_list.size

        # 12 readings per hour for 24 h = 288 readings per day
        # 288 readings per day for 30 days = 8640
        if (self.ext_temp_array_size >= array_size_limit):
            divisor = array_size_limit
            # if array size is at limit, remove the oldest value
            self.last_month_ext_temp_list = np.delete(self.last_month_ext_temp_list, 0)
        else:
            divisor = self.ext_temp_array_size

        # DOes cumulative sum - Last value is sum of all values in array
        cumsum = np.cumsum(self.last_month_ext_temp_list)
        cum_sum_last_month_ext_temp = cumsum[-1]

        # print ("Ext Temp Array size:", self.ext_temp_array_size)

        # print (c)
        #  print("CUrrent reading external Temp:",current_ext_temp )
        # print("Average monthly mean external temp:", (cum_sum_last_month_ext_temp) / divisor)

        return ((cum_sum_last_month_ext_temp) / divisor)

    def end(self):
        self.myMqtt.stop()

    # This is just a local temp and humid controller, there is a central controller making
    # decisions based on all input like tmp, humid, wind and dust
    def local_temp_test_controller(self):

        # house_id = self.getIDfromRC(rc_base_url,'getHID4pi:',local_ip_addr)
        internal_temp_topic = 'house/' + self.house_id + '/sensor/temp/internal'
        internal_RH_topic = 'house/' + self.house_id + '/sensor/rhumidity/internal'

        self.myMqtt.mySubscribe('/wunderground/temp/Turin', '/wunderground/wind/Turin', '/wunderground/weather/Turin',
                                '/wunderground/rhumidity/Turin',
                                internal_temp_topic, internal_RH_topic, 2)

        wind_multiplier = 1.0
        humid_multiplier = 1.0
        RH_lower_limit = 10.0
        RH_upper_limit = 10.0
        comf_temp_range = 7.5

        # Getting INITAL THRESHOLDS FOR TEMP - after entering loop- adaptive modelling kicks in
        l_threshold_temp = float(self.thresholdValuesFromCentre(self.cc_base_url, self.house_id, "init_temp_low"))
        u_threshold_temp = float(self.thresholdValuesFromCentre(self.cc_base_url, self.house_id, "init_temp_high"))

        while True:

            # getting the following thresholds every five mins from centre
            RH_lower_limit = float(self.thresholdValuesFromCentre(self.cc_base_url, self.house_id, "init_RH_low"))
            RH_upper_limit = float(self.thresholdValuesFromCentre(self.cc_base_url, self.house_id, "init_RH_high"))
            comf_temp_range = float(self.thresholdValuesFromCentre(self.cc_base_url, self.house_id, "tempRange"))

            # Higher the window multiplier value, better it is to open window
            # Check if outside conditions(excluding temp) allow opening of window and by how much
            if self.external_weather > 0:
                # Wind speed classification based on : https://www.windows2universe.org/earth/Atmosphere/wind_speeds.html

                if self.external_wind <= 1.0:
                    wind_multiplier = 1
                elif 1.1 <= self.external_wind <= 5.9:
                    wind_multiplier = 2
                elif 6.0 <= self.external_wind <= 11.9:
                    wind_multiplier = 3
                elif 12.0 <= self.external_wind <= 19.9:
                    wind_multiplier = 4
                elif self.external_wind > 20.0:
                    wind_multiplier = 0

            if (40.0 <= self.external_rHumidity <= 50.0):
                humid_multiplier = 1.25
            elif (35.0 <= self.external_rHumidity <= 55.0):
                humid_multiplier = 1.15
            elif (30.0 <= self.external_rHumidity <= 60.0):
                humid_multiplier = 1.0
            elif (25.0 <= self.external_rHumidity <= 65.0):
                humid_multiplier = 0.75
            elif (RH_lower_limit <= self.external_rHumidity <= RH_upper_limit):
                humid_multiplier = 0.5
            else:
                humid_multiplier = 0

            # If internal humidity is very bad, and outdoor RH is not very bad, even better to open window
            if (20.0 <= self.internal_rhumidity >= 70.0):
                humid_multiplier = humid_multiplier * 2

            # Impact of outside temperature on inside temperature
            ######### ASHRAE standard for thermal comfort #############
            # http://www.sciencedirect.com/science/article/pii/S2095263513000320
            # 12 readings per hour for 24 h = 288 readings per day
            # 288 readings per day for 30 days = 8640
            # So array size is being set to 8640 for taking monthly mean
            self.runningMonthMeanOutTemp = self.running_mean(self.external_temp, 8640)
            tComf = 0.31 * (self.runningMonthMeanOutTemp) + 17.8
            # Range on both sides from comf temp provided from central config file
            print "tComf:", tComf
            # print "comf_temp_range:",comf_temp_range
            self.l_threshold_temp = float(tComf) - comf_temp_range
            self.u_threshold_temp = float(tComf) + comf_temp_range

            print"int temp:", self.internal_temp
            print"internal_rhumidity:", self.internal_rhumidity
            print"external temp:", self.external_temp
            print"external_rHumidity:", self.external_rHumidity
            print"external_wind:", self.external_wind
            print"runningMonthMeanOutTemp:", self.runningMonthMeanOutTemp
            print"lower threshold temp:", self.l_threshold_temp
            print"higher threshold temp:", self.u_threshold_temp

            print("____________________________________________________")
            if self.l_threshold_temp <= self.external_temp <= self.u_threshold_temp:
                self.window = 1

                print "External temp ok - open window"
            # <editor-fold desc="Description">
            # elif (self.l_threshold_temp > self.internal_temp):
            #     self.window = 0.5
            #
            #     print "EXT and INT temp both not ok-int lower than lower_threshold, opening window doesn't have major negative impact - open window"
            #
            #
            # elif (self.u_threshold_temp < self.internal_temp):
            #     self.window = 0.5
            #
            #     print "EXT and INT temp both not ok-int higher than higher_threshold, opening window doesn't have major negative impact - open window"
            # # </editor-fold>

            else:
                self.window = 0

                print "EXT temp NOT ok,Negative impact if window opened - Close Window"

            print("___________________________________________________")

            print "window value based only on temp:", self.window
            self.window = self.window * wind_multiplier
            print "window value based  on temp,wind:", self.window
            self.window = self.window * humid_multiplier
            print "window value based  on temp,wind,humidity:", self.window

            print("***************************************************")

            self.myMqtt.myPublish(str(self.house_id), str(self.window))
            print "window: " + str(self.window)
            print("****************************************************")

            time.sleep(30)

    def notify(self, topic, msg):
        # print msg
        if topic == "/wunderground/temp/Turin":
            self.external_temp = (json.loads(msg)['value'])

        if "/sensor/temp/internal" in topic:
            internal_temp_temporary = (json.loads(msg)['value'])
            if (internal_temp_temporary != "-100"):
                self.internal_temp = internal_temp_temporary
                # checking if we have value from sensor, if not skip and use default value
            else:
                self.internal_temp = 0

        if "/sensor/rhumidity/internal" in topic:
            internal_rhumidity_temporary = (json.loads(msg)['value'])
            # checking if we have value from sensor, if not skip and use default value
            if (internal_rhumidity_temporary != "-1"):
                self.internal_rhumidity = internal_rhumidity_temporary
            else:
                self.internal_rhumidity = 0

        if topic == "/wunderground/wind/Turin":
            self.external_wind = float((json.loads(msg)['value']))

        if topic == "/wunderground/weather/Turin":
            self.external_weather = (json.loads(msg)['value'])

        if topic == "/wunderground/rhumidity/Turin":
            self.external_rHumidity = (json.loads(msg)['value'])

            # print "received under topic %s" % (topic)


if __name__ == "__main__":
    start_TH_control = StartTempHumidMqtt()
    start_TH_control.local_temp_test_controller()
    # time.sleep(30)
    # test.end()
