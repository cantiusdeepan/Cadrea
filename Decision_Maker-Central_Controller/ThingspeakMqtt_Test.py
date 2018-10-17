# from __future__ import print_function
# from database import Packet
import requests
import json
import datetime
import paho.mqtt.publish as publish
import time
import ssl
import urllib2


class Thingspeak_MQTT:

    #pass
    def mqttConnection(self, channelID_APIKEY,p1,p2,p3,p4,p5,p6,p7,p8):

        try:
            words=channelID_APIKEY.split("_")
            channelID = words[0]
            APIKEY = words[1]

            #print"channelID:",channelID
            #print"APIKEY:", APIKEY
            topicText = 'channels/' + channelID + '/publish/' + APIKEY
            baseURL = 'https://api.thingspeak.com/update?api_key='+APIKEY

            #print"topicText:", topicText
            #print"baseURL:", baseURL

        except:
            print("Error in splitting TS CHannel ID and API key, possible problem in Resource catalog")
            pass

        print "Inside MQTT class"
        #  MQTT Connection Methods

        # Set useUnsecuredTCP to True to use the default MQTT port of 1883
        # This type of unsecured MQTT connection uses the least amount of system resources.
        useUnsecuredTCP = False

        # Set useUnsecuredWebSockets to True to use MQTT over an unsecured websocket on port 80.
        # Try this if port 1883 is blocked on your network.
        useUnsecuredWebsockets = False

        # Set useSSLWebsockets to True to use MQTT over a secure websocket on port 443.
        # This type of connection will use slightly more system resources, but the connection
        # will be secured by SSL.
        useSSLWebsockets = False

        #the easy WAYYYY

        directAPIkey = True

        ###   End of user configuration   ###


        # The Hostname of the ThingSpeak MQTT service
        mqttHostID = 'mqtt.thingspeak.com'

        # Set up the connection parameters based on the connection type
        if useUnsecuredTCP:
            tTransport = "tcp"
            tPort = 1883
            tTLS = None

        if useUnsecuredWebsockets:
            tTransport = "websockets"
            tPort = 80
            tTLS = None

        if useSSLWebsockets:
            tTransport = "websockets"
            tTLS = {'ca_certs': "/etc/ssl/certs/ca-certificates.crt", 'tls_version': ssl.PROTOCOL_TLSv1}
            tPort = 443


            # Create the topic string







        try:

            # build the payload string
            tPayload = "field1=" + str(p1) + "&field2=" + str(p2)  + "&field3=" + str(p3) + "&field4=" + str(p4) + \
                       "&field5=" + str(p5) + "&field6=" + str(p6) + "&field7=" + str(p7) + "&field8=" + str(p8)

            #print "payload: " + tPayload

        except:
            print ("Error while accessing param values in thingspeak mqtt ")
        # attempt to publish this data to the topic
        try:

            #print"topicText1:", topicText
            #print"baseURL1:", baseURL

            if (directAPIkey):

                 f = urllib2.urlopen(baseURL +"&" + tPayload)

                 #print f.read()

                 f.close()
            else:
                publish.single(topicText, payload=tPayload, hostname=mqttHostID, port=tPort, tls=tTLS, transport=tTransport)


        except:
            print("There was an error while publishing the data to thingspeak")



            # time.sleep(3)

        return 0

        # def channelIDretrieve(self,truckID):
        #     channels = requests.get("https://api.thingspeak.com/users/s201586/channels.json").content
        #     channels_json = json.loads(channels)
        #
        #     for ch in channels_json["channels"]:
        #         if ch.get("name") == str(truckID):
        #             return str(ch.get("id"))


if __name__ == '__main__':
    t = Thingspeak_MQTT()
    # idchannel = t.channelIDretrieve(1)
    # print (idchannel)
    t.mqttConnection(0, 0, 0)
