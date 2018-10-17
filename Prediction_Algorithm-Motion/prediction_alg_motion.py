#Motion prediction Web service
#Gets real-time motion values and then sends the prediction of motion for the next time instant
#Communication is via MQTT

import json
import time
import paho.mqtt.client as MQTT
import random
import fpformat
import numpy
from datetime import datetime

# It writes the weeks in a nested list called year[] with:
# num_weeks - number of weeks (for easier presentation we use 4, for the final product it would be 52)
# samples_week - how many samples per week (for easier presentation we use 20, for the final product it would be 336 - every half hour)
# new_week stores the values of motion in real time, got via an MQTT subscription


new_value = 5
#num_weeks = 52
#samples_week = 336
num_weeks = 4
samples_week = 20
new_week = []
prediction = []

#Making the matrix which will keep values for the whole year
year = []
for row in range(num_weeks):
    week = []
    for column in range(samples_week):
        week.append(random.randint(0, 1))
    year.append(week)
print year


#Defining the MQTT class with its methods. This code will subscribe to values from the motion sensor and publish prediction values.
class MyMQTT:
    def __init__(self, broker, port, notifier):
        self.broker = broker
        self.port = port
        self.notifier = notifier
        self._paho_mqtt = MQTT.Client("Prediction_alg_motion", False)
        self._paho_mqtt.on_connect = self.myOnConnect
        self._paho_mqtt.on_message = self.myOnMessageReceived

    def myOnConnect (self, paho_mqtt, userdata, flags, rc):
        print ("Connected to message broker with result code: "+str(rc))

    def myOnMessageReceived (self, paho_mqtt , userdata, msg):
        self.notifier.notify(msg.topic, msg.payload)
        print ("Message received. Message: " + msg.topic + " QoS: " + str(msg.qos) + " Payload: " + str(msg.payload))

    def myPublish(self,p,hid):
       print("barbastruzzo")
       js = {"data": "motion", "value": p}
       motion_topic = 'house/'+hid+'/prediction_local_controller/predict_motion'
       #motion_topic = 'house/' + hid + '/motion_local_controller/motion_status'
       self._paho_mqtt.publish(motion_topic, json.dumps(js), 2)

    def mySubscribe(self, topic, qos=2):
        self._paho_mqtt.subscribe(topic, qos)
        print "Subscription successful"

    def start(self):
        self._paho_mqtt.connect(self.broker, self.port)
        self._paho_mqtt.loop_start()

    def stop(self):
        self._paho_mqtt.loop_stop()




class DoSomething():
    def __init__(self):
    	print "hello"
        self.house_id = ""
        self.mqtt_broker = ""
        self.mqtt_port = 0
        self.RC_config_reader()
        self.myMqtt = MyMQTT(self.mqtt_broker, self.mqtt_port, self)
        #self.myMqtt = MyMQTT("192.168.1.105", self.mqtt_port, self)
        self.myMqtt.start()
        self.myMqtt.mySubscribe('house/'+self.house_id+'/motion_local_controller/motion_status',0)
        global new_week
        global samples_week
        global week
        global year
        global num_weeks
        global prediction
        self.count = 0

        print "Old year: ", year
        self.predict()

        while True:

            time.sleep(30)

            new_week.append(new_value)
            print "new week is: ", new_week
            if len(new_week) == samples_week:
                print "Weeks shift here. New_week becomes the last week and is then emptied."
                for i in range(num_weeks):
                    if (i == num_weeks-1):
                        year[i] = new_week
                        break
                    year[i] = year[i+1]

                print "New year: ", year
                obj_year = {"year": year}
                self.writejson("predictions.json", obj_year)
                #break
                new_week = []
                self.count=0

                #trying to get the predictions
                self.predict()

#We publish a predicted value every half-hour
            self.myMqtt.myPublish(prediction[self.count], self.house_id)
            print "I've published at time: ", str(datetime.now())
            self.count += 1


#With this method we predict the presence values based on values for that time of the day and week, throughout the whole year
#We do it using a weighted average algorithm in which we use a number of past values, where the more recent values have a higher weight in the prediction

    def predict(self):
        global prediction
        #emptying prediction vector
        prediction = []
        #making column vectors with the appropriate values
        columns = []
        for row in range(samples_week):
            help = []
            for column in range(num_weeks):
                help.append(0)
            columns.append(help)

        for i in range(samples_week):
            for j in range(num_weeks):
                columns[i][j] = year[j][i]

        print "columns: ", columns

        for m in range(samples_week):
            x = 0
            sum_weights = 0
            weight = 0.5
            for item in columns[m]:
                x += (item * weight)
                sum_weights += weight
                weight += 0.1

            result = x / sum_weights
            print "Result: ", result
            if (result > 0.49999):
                prediction.append(1)
            else:
                prediction.append(0)
        print "Prediction: ", prediction


    def writejson(self, filename, obj):
        myfile = open(filename, "w")
        obj_1 = obj
        json.dump(obj_1, myfile)
        myfile.close()

    def end(self):
        self.myMqtt.stop ()

    def RC_config_reader(self):

        json_file = open('prediction_config.json').read()
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

    def notify(self, topic, msg):
        global new_value
        global num_weeks
        global samples_week
        global prediction
        if topic=='house/'+self.house_id+'/motion_local_controller/motion_status':
            new_value=(json.loads(msg)['value'])
        print "I've received the new value and it is: ", new_value



if __name__ == "__main__":
    test = DoSomething()
    test.end()