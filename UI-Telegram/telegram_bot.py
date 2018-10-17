import time
import telepot
import json
import paho.mqtt.client as PahoMQTT
import paho.mqtt.publish as publish
import requests
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

sensor_list = {}
rc_base_url = ""
cc_base_url = ""
holiday_mode = False

def myOnConnect( paho_mqtt, userdata, flags, rc):
    print ("Connected to message broker with result code: " + str(rc))

def myOnMessageReceived(paho_mqtt, userdata, msg):
    global rc_base_url
    global cc_base_url

    # A new message is received
    print ("Message: " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    payload_json = json.loads(msg.payload)                          #^^^ house_id^^^
    if payload_json["value"] == 1: #QUI DISTINGUERE I MESSAGGI DA INVIARE A SECONDA DEL TOPIC (msg.topic)
        rc_base_url, cc_base_url = getURLs(False)
        house_id = str(msg.topic).split("/")[1]
        telegram_users = getIDfromRC(rc_base_url, "getTelUsersList4HID:", house_id) #getSensorList4HID
                                #"http://192.168.1.100:8080"
        sendBroadcastMessage(telegram_users)

def getIDfromRC(url, command, param):
    data=command+param
    try:
        response = requests.post(url, data=data)
        return response.text
    except:
        print("Error in fetching data from resource catalog:", data)
        pass

def getURLs(mqtt): #whether the method is called to enstablish a mqtt connection or retrieve data from the RC
    global rc_base_url
    global cc_base_url
    rc_base_url = ""
    cc_base_url = ""
    try:
        if mqtt == False:
            with open('bot_config.json', 'r') as json_data_file:
                local_config = json.load(json_data_file)
            # local_config = json.loads(json_file)
            if local_config.get("RC_base_url"):
                rc_base_url = local_config["RC_base_url"]
            else:
                print "Problem in local json - Can't get RC url"

            if local_config.get("Central_config_base_url"):
                cc_base_url = local_config["Central_config_base_url"]
            else:
                print "Problem in local json - Can't get Central config url"
            return rc_base_url, cc_base_url

        else:
            with open('bot_config.json', 'r') as json_data_file:
                local_config = json.load(json_data_file)
            if local_config.get("mqtt_broker"):
                mqtt_url = local_config["mqtt_broker"]
            else:
                print "Problem in local json - Can't get broker url"

            if local_config.get("mqtt_port"):
                mqtt_port = local_config["mqtt_port"]
            else:
                print "Problem in local json - Can't get broker port"
            return mqtt_url, mqtt_port
    except:
        print("Cannot load 'bot_config.json'")
        pass

def sendBroadcastMessage(users_list):
    users_list = users_list.split(",")
    users_list.pop()
    for chat_id in users_list:
        bot.sendMessage(chat_id, 'Gas leak detected.')

def on_chat_message(msg):
    global sensor_list
    sensor_list = []
    holiday_list = []
    rc_base_url, cc_base_url = getURLs(False)
    holiday_flag = False

    content_type, chat_type, chat_id = telepot.glance(msg)
    print('Chat:', content_type, chat_type, chat_id, msg['text'])
    #print bot.getUpdates()'''

    temp = [InlineKeyboardButton(text='Current Temperature', callback_data='temp')]
    humid = [InlineKeyboardButton(text='Current Humidity', callback_data='humid')]
    dust = [InlineKeyboardButton(text='Current Air Quality', callback_data='dust')]
    purifier = [InlineKeyboardButton(text='Purifier status', callback_data='purifier')]
    window = [InlineKeyboardButton(text='Window status', callback_data='window')]
    #gas = [InlineKeyboardButton(text='Current Gas Level', callback_data='gas')]

    if content_type == "text" and u'\U0001f44b' in msg['text']: #choose the command
        on_holiday_mode = [InlineKeyboardButton(text='Yes', callback_data='holiday_on')]
        off_holiday_mode = [InlineKeyboardButton(text='No', callback_data='holiday_off')]
        holiday_list.append(on_holiday_mode)
        holiday_list.append(off_holiday_mode)
        holiday_flag = True

    try:
        house = getIDfromRC(rc_base_url, "getHID4TeID:", str(chat_id))
        #retieve sensors list from the RC,          command,                    house id
        sensor_dict = getIDfromRC(rc_base_url, "getSensorList4HID:", str(house)) #str(msg.topic).split("/")[1]
        sensor_dict = sensor_dict.split(",")
        for item in sensor_dict:
            if item == "TH":
                sensor_list.append(temp)
                sensor_list.append(humid)
                continue
            if item == "D": #
                sensor_list.append(dust)
                continue
            #if item == "G":
                #sensor_list.append(gas)
                #continue
        sensor_list.append(purifier)
        sensor_list.append(window)

        if holiday_flag:
            keyboard2 = InlineKeyboardMarkup(inline_keyboard=holiday_list)
            bot.sendMessage(chat_id, "Do you want to activate the Holiday Mode?", reply_markup=keyboard2)
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=sensor_list)
            bot.sendMessage(chat_id, "What information you'd like to know?", reply_markup=keyboard)
        #bot.sendMessage(chat_id, "What information you'd like to know?", reply_markup=keyboard)
    except:
        print("Error in fetching data from resource catalog: ', 'getSensorList4HID': "+str(chat_id))
        pass


def on_callback_query(msg):
    global holiday_mode
    query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
    print('Callback Query:', query_id, from_id, query_data)

    try:

        if query_data is not None:#and (query_data=='temp' or query_data=='humid')

            house = getIDfromRC(rc_base_url, "getHID4TeID:", str(from_id)) #get house id from user telegram chat id
            ts_channel = getIDfromRC(rc_base_url, "getTSCID4HID:", str(house)) #returns 250195_7JMAC5PPKE7M36JX
            sensor_data = requests.get("https://api.thingspeak.com/channels/"+str(ts_channel.split("_")[0])+"/feed.json?results=1")
            sensor_data = json.loads(sensor_data.text)
            sensor_data = sensor_data['feeds'][0]

            if query_data=='temp':
                reply_string='Current Temperature: '+sensor_data['field1']
            if query_data == 'humid':
                reply_string = 'Current Humidity: '+sensor_data['field2']
            if query_data == 'dust':
                reply_string = 'Current Air Quality: '+sensor_data['field4']
            if query_data == 'purifier':
                print "in"
                if sensor_data['field7'] == "0":
                    reply_string = 'The purifier is currently turned off'
                elif sensor_data['field7'] == "1":
                    reply_string = 'The purifier is currently turned on'
            if query_data == 'window':
                if sensor_data['field8'] == "0":
                    reply_string = 'The window is currently not opened'
                elif sensor_data['field8'] == "1":
                    reply_string = 'The window is currently opened'
            if query_data == 'holiday_on':
                reply_string = 'Holiday Mode activated'
                holiday_mode = True
                topic = 'house/' + str(house) + '/telegram_controller/vacation_mode'
                _paho_mqtt.publish(topic, 1, 2)
            if query_data == 'holiday_off':
                reply_string = 'Holiday Mode deactivated'
                holiday_mode = False
                topic = 'house/' + str(house) + '/telegram_controller/vacation_mode'
                _paho_mqtt.publish(topic, 0, 2)

            bot.sendMessage(from_id,reply_string)
    except:
        print("Error in fetching data from resource catalog: ', 'getHID4TeID', 'getTSCID4HID'")
        pass

TOKEN =  '341609228:AAHFnuyfgPoGHoOGsTYNht0rJnhbsVjaUmk'  # get token from command-line

bot = telepot.Bot(TOKEN)
bot.message_loop({'chat': on_chat_message,
                  'callback_query': on_callback_query})
print('Listening ...')

rc_base_url, cc_base_url = getURLs(False)
mqtt_url, mqtt_port = getURLs(True)
try:
    _paho_mqtt = PahoMQTT.Client("gas_leak", True)
    _paho_mqtt.on_connect = myOnConnect
    _paho_mqtt.on_message = myOnMessageReceived
    # _paho_mqtt.connect('iot.eclipse.org', 1883)
    # _paho_mqtt.connect(str(rc_url), int(rc_port))
    _paho_mqtt.connect(mqtt_url, mqtt_port)
    _paho_mqtt.loop_start()
except:
    print("Error connecting to MQTT Broker.")
    pass

while True:
    try:
        #_paho_mqtt.subscribe("$SYS/broker/clients/total", 2)
        _paho_mqtt.subscribe("house/+/gas_local_controller/gas_window", 2)
        time.sleep(5)
    except:
        print("Error ")
        pass
