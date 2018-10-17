import random
import string
import json
import requests
import paho.mqtt.client as MQTT
import time


class MyMQTT:
    def __init__(self, broker, port, notifier):
        self.broker = broker
        self.port = port
        self.notifier = notifier
        self._paho_mqtt = MQTT.Client("Ext_weather_publisher", False)
        self._paho_mqtt.on_connect = self.myOnConnect
        self._paho_mqtt.on_message = self.myOnMessageReceived

    def myOnConnect(self, paho_mqtt, userdata, flags, rc):
        print ("Connected to message broker with result code: " + str(rc))

    def myOnMessageReceived(self, paho_mqtt, userdata, msg):
        self.notifier.notify(msg.topic, msg.payload)

    def myPublish(self, wTemp, wWind, wWeather, wHumid):
        # print("barbastruzzo")
        #wTemp=20.0
        wHumid = 50.0

        js = {"data": "wund_Temp", "value": wTemp}
        self._paho_mqtt.publish('/wunderground/temp/Turin', json.dumps(js), 2)
        js1 = {"data": "wund_Wind", "value": wWind}
        self._paho_mqtt.publish('/wunderground/wind/Turin', json.dumps(js1), 2)
        js2 = {"data": "wund_Weather", "value": wWeather}
        self._paho_mqtt.publish('/wunderground/weather/Turin', json.dumps(js2), 2)
        js2 = {"data": "wund_Weather", "value": wHumid}
        self._paho_mqtt.publish('/wunderground/rhumidity/Turin', json.dumps(js2), 2)

        print("Publishing Wunderground data on MQTT")

    # self._paho_mqtt.publish(topic, msg, qos)

    def mySubscribe(self, topic, topic2, qos=2):
        self._paho_mqtt.subscribe(topic, qos)
        self._paho_mqtt.subscribe(topic2, qos)

    def start(self):
        self._paho_mqtt.connect(self.broker, self.port)
        self._paho_mqtt.loop_start()

    def stop(self):
        self._paho_mqtt.loop_stop()


class ParsePublishWunderData():
    def __init__(self):
        self.myMqtt = MyMQTT('192.168.1.73', 1883, self)
        self.myMqtt.start()
        self.wunderMain()
        self.getLocalConfig()
        self.myMqtt = MyMQTT(self.mqtt_broker, self.mqtt_port, self)

    def getLocalConfig(self):
        json_file = open('local_Wunder_Config.json').read()
        local_config = json.loads(json_file)


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

    def getDataFromWunderground(self, my_string, wunderJSON):

        try:

            print wunderJSON["current_observation"][my_string]

            return wunderJSON["current_observation"][my_string]
        except:
            print "error in parsing wunderJSON"
            pass

    def getWunderground(self):
        url = 'http://api.wunderground.com/api/b18bedd5595f4d5d/conditions/q/italy/Turin.json'
        hourlyForecastURL = 'http://api.wunderground.com/api/b18bedd5595f4d5d/hourly/q/italy/Turin.json'

        try:
            response = requests.post(url)
            return response.json()
        except:
            print("Error in fetching WunderData")
            pass



    def wunderMain(self):
        # List set manually by checking available weather condition from wunderground api
        stopEXTWeatherList = ["Thunderstorm", "Dust", "Sand", "Rain", "Ash", "Smoke", "Fog", "Smog"]

        external_condition = 0
        while True:
            wUnderground = self.getWunderground()
            external_temp = self.getDataFromWunderground("temp_c", wUnderground)
            external_wind = self.getDataFromWunderground("wind_kph", wUnderground)
            external_condition_string = self.getDataFromWunderground("weather", wUnderground)
            external_RH_string = self.getDataFromWunderground("relative_humidity", wUnderground)

            # external_temp = 31.0
            # external_wind = 5.0
            # external_condition_string = 'Clear'
            # external_RH_string = '59%'

            # Convert strings to be compared to uppercase to avoid issues due to mismatch only in case
            if any(x in external_condition_string for x in stopEXTWeatherList):
                external_condition = 0
                print "OUTSIDE WEATHER NOT GOOD - DON'T OPEN WINDOW"
            else:
                external_condition = 1
                print "Opening window is fine"

            external_RH = float(external_RH_string.rstrip('%'))
            print "External Temp:", external_temp
            print "External Wind:", external_wind
            print "External Weather:", external_condition
            print "External RH:", external_RH

            time.sleep(30)

            self.myMqtt.myPublish(external_temp, external_wind, external_condition, external_RH)
            #self.myMqtt.myPublish(10.0, 20.0, 1, 77.0)



if __name__ == "__main__":
    test = ParsePublishWunderData()
