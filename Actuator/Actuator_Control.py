
import json
import time
import paho.mqtt.client as MQTT
import RPi.GPIO as GPIO


class MyMQTT:
    def __init__(self, broker, port, notifier):
        self.broker = broker
        self.port = port
        self.notifier = notifier
        self._paho_mqtt = MQTT.Client("Actuator_controller_main", True)
        self._paho_mqtt.on_connect = self.myOnConnect
        self._paho_mqtt.on_message = self.myOnMessageReceived

    def myOnConnect(self, paho_mqtt, userdata, flags, rc):
        pass

    def myOnMessageReceived(self, paho_mqtt, userdata, msg):
        #print("Inside message received")
        self.notifier.notify(msg.topic, msg.payload)

    def myPublish(self, w,p, housIDvar):
        # print("barbastruzzo")
        js = {"data": "final_window", "value": w}
        topic = 'house/'+ housIDvar + '/central_controller/final_window'
        self._paho_mqtt.publish(topic, json.dumps(js), 2)
        js = {"data": "final_purifier", "value": p}
        topic = 'house/'+ housIDvar + '/central_controller/final_purifier'
        self._paho_mqtt.publish(topic, json.dumps(js), 2)


    # self._paho_mqtt.publish(topic, msg, qos)

    def mySubscribe(self, decision_window_topic, decision_purifier_topic, decision_vacation_topic, qos=2):
        self._paho_mqtt.subscribe(decision_window_topic, qos)
        self._paho_mqtt.subscribe(decision_purifier_topic, qos)
        self._paho_mqtt.subscribe(decision_vacation_topic, qos)


    def start(self):
        self._paho_mqtt.connect(self.broker, self.port)
        self._paho_mqtt.loop_start()

    def stop(self):
        self._paho_mqtt.loop_stop()


class StartActuatorController():

    def __init__(self):
        #####Values to be fetched from local config

        self.house_id = 0
        self.mqtt_broker = ""
        self.mqtt_port = 0

        self.getLocalConfig()

        self.myMqtt = MyMQTT(self.mqtt_broker, self.mqtt_port, self)
        self.myMqtt.start()

        ##Decision make input variables
        self.vacation_value = 0
        self.window_value = 0
        self.purifier_value = 0

        self.actuator_controller()

    def getLocalConfig(self):
        json_file = open('local_actuator_config.json').read()
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

    def actuate(self):

         #GPIO(BCM) - 18 - Purifier, 5- Window
         GPIO.setmode(GPIO.BCM)
         GPIO.setwarnings(False)

         if(self.purifier_boolean):
             GPIO.setup(18, GPIO.OUT)
             print "Purifier on"
             GPIO.output(18, GPIO.HIGH)
         else:
             print "Purifier off"

             GPIO.setup(18, GPIO.IN,pull_up_down = GPIO.PUD_DOWN)
         if (self.window_boolean):
             GPIO.setup(5, GPIO.OUT)
             print "Window on"
             GPIO.output(5, GPIO.HIGH)
         else:
             print "Window off"

             GPIO.setup(5, GPIO.IN,pull_up_down = GPIO.PUD_DOWN)


    def end(self):
        self.myMqtt.stop()

    def actuator_controller(self):


        ###Values required for decision making
        decision_window_topic =  'house/'+ str(self.house_id) + '/central_controller/final_window'
        decision_purifier_topic = 'house/' + str(self.house_id) + '/central_controller/final_purifier'
        decision_vacation_topic = 'house/' + str(self.house_id) + '/telegram_controller/vacation_mode'




        self.myMqtt.mySubscribe(decision_window_topic, decision_purifier_topic, decision_vacation_topic, 2)



        while True:


            print"window_value:", self.window_value
            print"purifier_value:", self.purifier_value
            print"vacation_value:", self.vacation_value

            if(self.vacation_value> 0):
                print("Vacation mode")

                self.window_value = 0
                self.purifier_value = 0

            if(self.window_value > 0):
                self.window_boolean = True
            else:
                self.window_boolean = False
            if(self.purifier_value > 0):
                self.purifier_boolean = True
            else:
                self.purifier_boolean = False

            self.actuate()
            time.sleep(15)


    def notify(self, topic, msg):

        ####Values for decision making
        if "final_window" in topic:
            self.window_value=int((json.loads(msg)['value']))


        if "final_purifier" in topic:
            self.purifier_value = int((json.loads(msg)['value']))


        if "vacation_mode" in topic:
            self.vacation_value = int(msg)
            print "received under vacation topic: %s" % (msg)


        #print "received under topic %s" % (topic)





if __name__ == "__main__":
    AC = StartActuatorController()
    # time.sleep(30)
    # test.end()
