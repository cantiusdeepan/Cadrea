import json
import time
import paho.mqtt.client as MQTT
import random
import fpformat


class MyMQTT:
    def __init__(self, broker, port, notifier):
        self.broker = broker
        self.port = port
        self.notifier = notifier
        self._paho_mqtt = MQTT.Client("data_inside", False)
        self._paho_mqtt.on_connect = self.myOnConnect
        self._paho_mqtt.on_message = self.myOnMessageReceived

    def myOnConnect (self, paho_mqtt, userdata, flags, rc):
        print ("Connected to message broker with result code: "+str(rc))

    def myOnMessageReceived (self, paho_mqtt , userdata, msg):
        self.notifier.notify (msg.topic, msg.payload)

    def myPublish(self, airValue,house_id):
       # print("barbastruzzo")
       js = {"data": "internalAir", "value": airValue}
       self._paho_mqtt.publish('house/'+house_id+'/sensor/dust/internal', json.dumps(js), 2)
    #self._paho_mqtt.publish(topic, msg, qos)

    def mySubscribe(self, topic,topic2,topic3, qos=2):
        self._paho_mqtt.subscribe(topic, qos)
        self._paho_mqtt.subscribe(topic2, qos)
        self._paho_mqtt.subscribe(topic3, qos)

    def start(self):
        self._paho_mqtt.connect(self.broker, self.port)
        self._paho_mqtt.loop_start()

    def stop(self):
        self._paho_mqtt.loop_stop()

class DoSomething():
    def __init__(self):
        self.window=0
        self.cleaner=0
        self.external_air=30
        self.mqtt_port=""
        self.mqtt_broker=""
        self.house_id=""
        self.getLocalConfig()
        self.myMqtt = MyMQTT(self.mqtt_broker, self.mqtt_port, self)
        self.myMqtt.start()
        self.myMqtt.mySubscribe('house/'+self.house_id+'/sensor/dust/external','house/'+ self.house_id+ '/central_controller/final_window','house/'+ self.house_id + '/central_controller/final_purifier',0)
        self.simulate_intenal_data()


    #def run(self):
     #   self.myMqtt.start()

    def end(self):
        self.myMqtt.stop ()

    def simulate_intenal_data(self):
        i=0;
        j=1;
        k=0
        #value= int(self.getValue(1,199))
        value=40.00
        print "value= " + str(value)
        while True:
            gas_value=value
            if self.window==0 and self.cleaner==0:
                interval=0.002
                if gas_value>self.external_air:
                    gas_value=gas_value-interval
                else:
                    gas_value=gas_value+interval
                value=gas_value
            if self.window==1 and self.cleaner==0:
                i=0
                interval=0.25
                #interval=float((external_air-gas_value)/100)
                #print str(interval)
                if self.external_air>gas_value:
                    gas_value = gas_value+interval
                else:
                    gas_value = gas_value - interval
                value=gas_value

            if self.window==0 and self.cleaner==1:
                interval=0.25
                gas_value=gas_value-interval
                value=gas_value

            if self.window == 1 and self.cleaner == 1:
                if self.external_air<gas_value:
                    interval=0.30
                else:
                    interval=0.10
                gas_value=gas_value-interval
                value=gas_value


            print("data= "+str(gas_value))
            self.myMqtt.myPublish(float(fpformat.fix(gas_value,3)),self.house_id)
            time.sleep(15)

    def getValue(self,a,b):
        return random.randint(int(a),int(b));

    def notify(self, topic, msg):
        if topic=="house/"+self.house_id+"/sensor/dust/external":
            self.external_air=float(json.loads(msg)['value'])
        if topic == "house/"+ self.house_id+ "/central_controller/final_window":
            self.window = int(json.loads(msg)['value'])
        if topic == "house/"+ self.house_id + "/central_controller/final_purifier":
            self.cleaner = int(json.loads(msg)['value'])
        print "received %s under topic %s" % (msg,topic)
       # print "externale air: "+self.external_air


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
          #  self.ChannelID_APIKEY = self.getIDfromRC(self.rc_base_url, 'getTSCID4HID:', self.house_id)


if __name__ == "__main__":
    test = DoSomething()
    #time.sleep(30)
    #test.end()