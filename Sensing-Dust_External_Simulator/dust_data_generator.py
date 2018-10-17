import json
import time
import paho.mqtt.client as MQTT
import random
import fpformat


class Dust_Data_Pubblisher:
    def __init__(self):
        self.mqtt_broker=""
        self.mqtt_port=""
        self.house_id=""
        self.getLocalConfig()
        self._pahoMotion=MQTT.Client("external_pollution", False)
        self._pahoMotion.on_connect = self.myOnConnect
        self._pahoMotion.connect(self.mqtt_broker, self.mqtt_port)
        self._pahoMotion.loop_start()
        self.simulate_external_data()

    def myPubblish(self,airValue):
        js={"data": "externalAir", "value": airValue}
        self._pahoMotion.publish('house/'+self.house_id+'/sensor/dust/external', json.dumps(js), 2)


    def myOnConnect(self, paho_mqtt, userdata, flags, rc):
        print ("Connected to message broker with result code: " + str(rc))

    def simulate_external_data(self):
        i=0;
        j=1;
        k=0
        #value= float(self.getValue(1,199))
        value=5.0
        dust_in=value
        print "value= " + str(value)
        while True:
            if i<80:
                #dust_in=0
                random_value=float(random.randint(-20,20))
                #print random_value
                random_value=random_value/100
                if dust_in+random_value<value+1 and dust_in+random_value>value-1:
                    dust_in=dust_in+random_value
                else:
                    if dust_in+random_value<value-1:
                        dust_in=value-1
                    if dust_in+random_value>value+1:
                        dust_in=value+1
                #print random_value
                gas_value=dust_in
                #gas_value=value+random_value#random.randint(value-1,value+1)
                i=i+1
            else:
                if value+5>200:
                    max=199
                    min=max-random.randint(6,9)
                elif value-5<1:
                    min=1
                    max=min+random.randint(6,9)
                else:
                    max=value+random.randint(3,5)
                    min=value-random.randint(3,5)
                value=self.getValue(min,max)
                if value>199:
                    value== 199
                elif value<1:
                    value==1
                j=j+1
                print "value= " + str(value)+ ", giro: "+str(j)
                gas_value = random.randint(value - 1, value + 1)
                i=0
                k=k+1
            print("data= "+str(gas_value))
            self.myPubblish(float(fpformat.fix(gas_value,2)))
            time.sleep(15)

    def getValue(self,a,b):
        return random.randint(int(a),int(b));

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


if __name__=="__main__":
    test=Dust_Data_Pubblisher()