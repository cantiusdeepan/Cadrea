import json
import time
import paho.mqtt.client as MQTT
import random
import fpformat
import requests
import socket



class MyMQTT:
    def __init__(self, broker, port, house_id, notifier):
        self.house_id=house_id
        self.broker = broker
        self.port = port
        self.notifier = notifier
        self._paho_mqtt = MQTT.Client("Dust_controller", True)
        self._paho_mqtt.on_connect = self.myOnConnect
        self._paho_mqtt.on_message = self.myOnMessageReceived

    def myOnConnect (self, paho_mqtt, userdata, flags, rc):
        print ("Connected to message broker with result code: "+str(rc))

    def myOnMessageReceived (self, paho_mqtt , userdata, msg):
        self.notifier.notify (msg.topic, msg.payload)

    def myPublish(self,w,c):
       #print("barbastruzzo")
       js = {"data": "window", "value": int(w)}
       self._paho_mqtt.publish('house/'+self.house_id+'/dust_local_controller/dust_window', json.dumps(js), 2)
       #self._paho_mqtt.publish('/options/window', json.dumps(js), 2)
       js = {"data": "cleaner", "value": int(c)}
       self._paho_mqtt.publish('house/'+self.house_id+'/dust_local_controller/purifier', json.dumps(js), 2)
       #self._paho_mqtt.publish('/options/cleaner', json.dumps(js), 2)

    def mySubscribe(self, topic,topic2, qos=2):
        self._paho_mqtt.subscribe(topic, qos)
        self._paho_mqtt.subscribe(topic2,qos)

    def start(self):
        self._paho_mqtt.connect(self.broker, self.port)
        self._paho_mqtt.loop_start()

    def stop(self):
        self._paho_mqtt.loop_stop()

class DoSomething():
    def __init__(self):
        self.mqtt_broker=""
        self.mqtt_port=""
        self.rc_base_url = ""
        self.cc_base_url = ""
        self.house_id = ""
        self.getLocalConfig()
        self.internal_th=20
        self.external_th=25
        self.internal_dust=50
        self.external_dust=100
        self.internal_th=float(self.thresholdValuesFromCentre(self.cc_base_url,self.house_id,"dust_in"))
        self.external_th=float(self.thresholdValuesFromCentre(self.cc_base_url,self.house_id, "dust_out"))
        self.myMqtt = MyMQTT(self.mqtt_broker, self.mqtt_port,self.house_id, self)
        self.myMqtt.start()
        self.myMqtt.mySubscribe('house/'+self.house_id+'/sensor/dust/external','house/'+self.house_id+'/sensor/dust/internal',2)
        self.dust_controller()

    def end(self):
        self.myMqtt.stop()

    def checking_dust(self):
        if self.internal_dust >= self.internal_th:
            cleaner = 1
            if self.external_dust >= self.external_th:
                window = 0
            else:
                if self.external_dust < self.internal_th:
                    window = 5
                else:
                    if self.external_dust < self.internal_dust:
                        window = 3
                    else:
                        window = 1
        else:
            cleaner = 0
            if self.external_dust >= self.external_th:
                window = 0
            else:
                if self.external_dust < self.internal_dust:
                    window = 5
                else:
                    if self.external_dust < self.internal_th:
                        window = 3
                    else:
                        window = 1
        return (window,cleaner)

    def dust_controller(self):
        time.sleep(10)
        while True:
            self.internal_th = float(self.thresholdValuesFromCentre(self.cc_base_url, self.house_id, "dust_in"))
            self.external_th = float(self.thresholdValuesFromCentre(self.cc_base_url, self.house_id, "dust_out"))
            #print "threshold " + str(self.internal_th)
            (win,clean)=self.checking_dust()
            self.myMqtt.myPublish(win, clean)
            print "window: "+ str(win)+ " cleaner: "+ str(clean)
            time.sleep(30)

    def notify(self, topic, msg):
        if topic=="house/"+self.house_id+"/sensor/dust/external":
            self.external_dust=(json.loads(msg)['value'])
        if topic == "house/"+self.house_id+"/sensor/dust/internal":
            self.internal_dust = (json.loads(msg)['value'])
        print "received %s under topic %s" % (msg,topic)

    def getLocalConfig(self):
        json_file = open('Dust_sensor_config.json').read()
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

           # self.ChannelID_APIKEY = self.getIDfromRC(self.rc_base_url, 'getTSCID4HID:', self.house_id)

    def thresholdValuesFromCentre(self, url, house_ID, reqString='index.html'):
        # URL of the GUIWebservice for Central config file
        # url = 'http://192.168.1.71:8081/'

        updated_url = url + house_ID + "/" + reqString
        print "updated_url:", updated_url
        try:
            response = requests.get(updated_url)
            print "threshold "+response.text
            return response.text
            #return response.text
        except:
            print("Error in fetching thingspeak ID from resource catalog")
            pass


if __name__ == "__main__":
    test = DoSomething()