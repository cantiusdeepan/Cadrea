# -*- coding: utf-8 -*-
import cherrypy
import os
import requests
import json
import mysql.connector as mc
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import collections

# threshold web service coordinates #
threshold_address = ""
try:
    with open('config_RC_WS.json', 'r') as json_data_file:
        obj = json.load(json_data_file)
        threshold_address = obj['threshold_web_service_url']
except:
    print("Error reading addresses from file.")
    pass
#portT = 8081
#urlT = '192.168.1.72'
###################################

port = 8080 #8081
url = '192.168.1.72' #192.168.1.72
#cherrypy.config.update({'server.socket_port': port})
cherrypy.config.update({'server.socket_host': url,
                       'server.socket_port': port,
                      })

house_chosen = ""
class RCWebService():

    exposed = True

    def GET(self, *uri, **params):

        if(uri[0] == "login.html"):
            return open("login_form.html")
        if(uri[0] == "add_house.html"):

            #house_ids = ["001", "002", "003"]
            try:
                data = "getHouseIDList"
                response = requests.post("http://192.168.1.71:8080", data=data)
                house_ids = response.text.split(",")
                house_ids.pop()
            except:
                print("Error in fetching data from resource catalog")
                pass

            max_id = ""
            if len(house_ids) > 0 and len(house_ids) < 9:
                max_id = "00"+str(len(house_ids)+1)
            elif len(house_ids) > 9 and len(house_ids) < 100:
                max_id = "0"+str(len(house_ids)+1)
            elif len(house_ids) > 100:
                max_id = str(len(house_ids)+1)

            #return open("add_house.html")
            return '''  <!DOCTYPE html>
                        <html>
                        <head>
                            <title>Add house</title>
                            <link rel="stylesheet" href="/static/style.css">
                            <meta charset="UTF-8">
                        </head>
                        <body>
                        <div id="wrapper">
                                <div id="banner"></div>
                            <h3>Enter the values:</h3>
                            <form method="post">
                                <h4>General information</h4>
                                <input type="text" value="add_house" id="add_house" name="add_house" readonly class="input2"><br>
                                <label for="house_name">Enter House name: </label>
                                <input id="house_name" name="house_name" class="input2"/><br>
                                <label for="local_pi_ip">Enter local raspberry ip address: </label>
                                <input id="local_pi_ip" name="local_pi_ip" class="input2"/><br>
                                <label for="house_id">Enter house id: </label>
                                <input id="house_id" name="house_id" class="input2" value="'''+str(max_id)+'''" readonly/><br>
                                <label for="telegram_users">Enter telegram chat_ids: </label>
                                <input id="telegram_users" name="telegram_users" class="input2"/>
                                <input id="telegram_users2" name="telegram_users2" class="input2"/>
                                <input id="telegram_users3" name="telegram_users3" class="input2"/>
                                <input id="telegram_users4" name="telegram_users4" class="input2"/><br>
                                <label for="thingspeak_id">Enter Thingspeak channel: </label>
                                <input id="thingspeak_id" name="thingspeak_id" class="input2"/><br>
                                <label for="freeboard">Enter Freeboard link: </label>
                                <input id="freeboard" name="freeboard" class="input2"/><br>
                                <label for="user_name">Enter user's username: </label>
                                <input id="user_name" name="user_name" class="input2"/><br>
                                <label for="pass_word">Enter user's password: </label>
                                <input id="pass_word" name="pass_word" class="input2"><br>
                                <label for="email">Enter user's email: </label>
                                <input id="email" name="email" class="input2"/><br>
                                <h4>Sensor list</h4>
                                <label for="sensor_0">Sensor: </label>
                                <input id="sensor_0" name="sensor_0" placeholder="sensor name" class="input2"/><br>
                                <label for="sensor_1">Sensor: </label>
                                <input id="sensor_1" name="sensor_1" placeholder="sensor name" class="input2"/><br>
                                <label for="sensor_2">Sensor: </label>
                                <input id="sensor_2" name="sensor_2" placeholder="sensor name" class="input2"/><br>
                                <label for="sensor_3">Sensor: </label>
                                <input id="sensor_3" name="sensor_3" placeholder="sensor name" class="input2"/><br>
                                <label for="sensor_4">Sensor: </label>
                                <input id="sensor_4" name="sensor_4" placeholder="sensor name" class="input2"/><br>
                                <label for="sensor_5">Sensor: </label>
                                <input id="sensor_5" name="sensor_5" placeholder="sensor name" class="input2"/><br>
                                <label for="sensor_6">Sensor: </label>
                                <input id="sensor_6" name="sensor_6" placeholder="sensor name" class="input2"/><br>
                                <label for="sensor_7">Sensor: </label>
                                <input id="sensor_7" name="sensor_7" placeholder="sensor name" class="input2"/><br>
                                <label for="sensor_8">Sensor: </label>
                                <input id="sensor_8" name="sensor_8" placeholder="sensor name" class="input2"/><br>
                                <label for="sensor_9">Sensor: </label>
                                <input id="sensor_9" name="sensor_9" placeholder="sensor name" class="input2"/><br><br>

                                <input type="submit" class="button1 button4"/>
                            </form>
                            <footer>
                                <p>All rights reserved ©
                                    </p>
                            </footer>
                            </div>
                        </body>
                        </html>'''

    def POST(self, *uri, **params):

        global house_chosen
        if params.get("house_id_list"):
            house_chosen = params.get("house_id_list")

        if params.has_key("username"):
            flag = 0
            #addr = "http://"+urlT+":"+str(portT)
            response = requests.post(threshold_address, "getDBItems")
            dict = json.loads(response.text)

            for item in dict['ids']:
                if item['house_id'] == "default" and flag == 0 and str(params['username']) == str(item['username']) and str(params['password']) == str(item['password']):
                    flag = 1 #trovato l'admin

            if flag == 1:
                house_ids = []
                try:
                   data = "getHouseIDList"
                   response = requests.post("http://192.168.1.71:8080", data=data)
                   house_ids = response.text.split(",")
                   house_ids.pop()
                except:
                   print("Error in fetching data from resource catalog")
                   pass

                drop_down_list = "<div class='dropdown-content'>"

                for id in house_ids:
                    drop_down_list = drop_down_list + "<option value='" + str(id) + "' class=''>" + str(id) + "</option>"
                drop_down_list = drop_down_list+"</div>"

                return '''  <!DOCTYPE html>
                            <html>
                            <head>
                                <title>Admin action</title>
                                <link rel="stylesheet" href="/static/style.css">
                            </head>
                            <body>
                            <div id="wrapper">
		                        <div id="banner"></div>
		                        <br>
                                <button id="add_h_btn" name="add_h_btn" onclick="location.reload();location.href='add_house.html'" class="button1 button4">Add new house</button>
                                <form  method="post">
                                <div class="dropdown">
                                <br>
                                <select name='house_id_list' id='house_id_list' class="dropbtn">'''+drop_down_list+''''</select>
                                <input type="submit" id="modify_h_btn" name="modify_h_btn" onclick="location.reload();location.href='modify_house.html'" class="button1 button4"/>
                                </div>
                                </form>
                                <br></br>
                                <br></br>
                                <br>
                                <footer>
                                    <p>All rights reserved ©</p>
                                </footer>
                                </div>
                            </body>
                            </html>'''
            else: return open("login_form.html")
        elif params.get("add_house"):

            sensors_dict = {}
            sensors_ids = ["010","009","008","007","006","005","004","003","002","001"]
            for key in sorted(params.keys()):
                if key == "sensor_0" and params.get(key) != "":
                    sensors_dict.update({sensors_ids.pop():{"sensor": str(params['sensor_0'])}})
                if key == "sensor_1" and params.get(key) != "":
                    sensors_dict.update({sensors_ids.pop():{"sensor": str(params['sensor_1'])}})
                if key == "sensor_2" and params.get(key) != "":
                    sensors_dict.update({sensors_ids.pop():{"sensor": str(params['sensor_2'])}})
                if key == "sensor_3" and params.get(key) != "":
                    sensors_dict.update({sensors_ids.pop():{"sensor": str(params['sensor_3'])}})
                if key == "sensor_4" and params.get(key) != "":
                    sensors_dict.update({sensors_ids.pop():{"sensor": str(params['sensor_4'])}})
                if key == "sensor_5" and params.get(key) != "":
                    sensors_dict.update({sensors_ids.pop():{"sensor": str(params['sensor_5'])}})
                if key == "sensor_6" and params.get(key) != "":
                    sensors_dict.update({sensors_ids.pop():{"sensor": str(params['sensor_6'])}})
                if key == "sensor_7" and params.get(key) != "":
                    sensors_dict.update({sensors_ids.pop():{"sensor": str(params['sensor_7'])}})
                if key == "sensor_8" and params.get(key) != "":
                    sensors_dict.update({sensors_ids.pop():{"sensor": str(params['sensor_8'])}})
                if key == "sensor_9" and params.get(key) != "":
                    sensors_dict.update({sensors_ids.pop():{"sensor": str(params['sensor_9'])}})

            print sensors_dict.keys()
            sensors = {"sensors":[]}

            for item in sorted(sensors_dict.keys()):
                d = {"sensor_type":str(sensors_dict.get(item)['sensor']),
                    "sensor_id":str(params['house_id'])+str(item)}
                sensors['sensors'].append(d)

            tel_users = []
            if params.get("telegram_users") and str(params.get("telegram_users")) != "":
                tel_users.append(params["telegram_users"])
            if params.get("telegram_users2") and str(params.get("telegram_users2")) != "":
                tel_users.append(params["telegram_users2"])
            if params.get("telegram_users3") and str(params.get("telegram_users3")) != "":
                tel_users.append(params["telegram_users3"])
            if params.get("telegram_users4") and str(params.get("telegram_user4")) != "":
                tel_users.append(params["telegram_users4"])

            dict = {"house_name": str(params['house_name']), "local_pi_ip": str(params['local_pi_ip']),
                    "house_id": str(params['house_id']),
                    "telegram_users": tel_users,
                    "sensors":sensors['sensors'], "latest_sensor_id": sensors['sensors'][-1]['sensor_id'],
		            "thingspeak_channel_ID": str(params['thingspeak_id'])}

            #QUI INVIARE dict AL RESOURCE catalog VIA REQUEST
            data = "addHJSON4HID"
            try:
                data = "addHJSON4HID*"+str(params['house_id'])+"*"+ json.dumps(dict)
                requests.post("http://192.168.1.71:8080", data=data)
            except:
                print("Error in fetching data from resource catalog:", data)
                pass

            #create database new entry
            try:             #"http://127.0.0.1:3032"
                #"http://"+urlT+":"+str(portT)
                requests.post(threshold_address,"setDBnewItem:"+params['user_name']+":"+params['pass_word']+":"+params['email']+":"+params['house_id'])
            except:
                print ("Error adding new entry into database.")
                pass

            #update the local threshold file too

            #questo potrei anche toglierlo, mi serve solo per tenere una versione aggiornata delle thresholds
            #nel mio local pc
            # da qui -----------------
            data = "addHouse2Thresholds*"
            new_house = {"telegram_users": tel_users, "freeboard": str(params['freeboard']),
                         "house_id": str(params['house_id'])}
            try:
                data = "addHouse2Thresholds*" + "default*" + json.dumps(new_house)
                requests.post("http://192.168.1.72:8081", data=data)
            except:
                print("Error in fetching data from resource catalog:", data)
                pass

            #with open('cc_webservice_config.json', 'r') as json_data_file:
            #    obj = json.load(json_data_file)
            #default_thres = {}
            #for house in obj['houses']:
            #   if house.get("house_id") == "default":
            #       default_thres.update(house['thresholds']) #dovre scegliere quali soglie mettere in base ai sensori inseriti
                                                              #ma ...
            #new_house = {"telegram_users": tel_users, "freeboard": str(params['freeboard']), "house_id": str(params['house_id']),
		    #"thresholds": default_thres}
            #obj['houses'].append(new_house)

            #with open('cc_webservice_config.json', 'w') as json_data_file:
            #    json.dump(obj, json_data_file)
            # a qui -----------------

            try:
                data = "getThreshObj"
                response = requests.post("http://192.168.1.72:8081", data=data)
            except:
                print("Error in fetching data from threshold webservice")
                pass

            return open("login_form.html")

        elif params.get("house_id_list"):

            data = "getFreeboardLink*"
            freeboard_link = ""
            try:
                data = "getFreeboardLink*" + str(params['house_id_list'])
                response = requests.post("http://192.168.1.72:8081", data=data)
                freeboard_link = response.text
            except:
                print("Error in fetching data from resource catalog:", data)
                pass

            #with open('cc_webservice_config.json', 'r') as json_data_file2:
            #    obj2 = json.load(json_data_file2)

            #freeboard_link = ""
            #for house in obj2['houses']:
             #   if house['house_id'] == params['house_id_list']:
            #        freeboard_link = house['freeboard']

            # OTTENERE DAL RC LE INFO DELLA CASA TRAMITE REQUEST, INVECE CHE COME FATTO GIU'
            house = {}
            data = "getHJSON4HID"
            try:
               data = "getHJSON4HID:"+str(params['house_id_list'])
               response = requests.post("http://192.168.1.71:8080", data=data)
               house = json.loads(response.text)
               print response.text
            except:
                print("Error in fetching data from resource catalog:", data)
                pass

            tel_users = {}
            for user in range(0,4): #4 max number of sensors
                if user < len(house['telegram_users']) and house['telegram_users'][user] != "":
                    tel_users.update({str(user):house['telegram_users'][user]})
                else:
                    tel_users.update({str(user):""})
            sensors_list = {}
            for sensor in range(0, 10): #10 max number of sensors
                if sensor < len(house['sensors']) and house['sensors'][sensor]['sensor_type'] != "":
                    sensors_list.update({str(sensor):house['sensors'][sensor]['sensor_type']})
                else:
                    sensors_list.update({str(sensor):""})

            return '''  <!DOCTYPE html>
                        <html>
                        <head>
                            <title>Add house</title>
                            <link rel="stylesheet" href="/static/style.css">
                            <meta charset="UTF-8">
                        </head>
                        <body>
                        <div id="wrapper">
		                <div id="banner"></div>
                            <h3>Enter the values</h3>
                            <form method="post">
                                <h4>General informations</h4>
                                <input type="text" value="modify_house" id="modify_house" name="modify_house" readonly class="input2"><br>
                                <label for="house_name">Enter House name</label>
                                <input id="house_name" name="house_name" value="'''+str(house['house_name'])+'''" class="input2"/><br>
                                <label for="local_pi_ip">Enter local raspberry ip address</label>
                                <input id="local_pi_ip" name="local_pi_ip" value="'''+str(house['local_pi_ip'])+'''" class="input2"/><br>
                                <label for="house_id">Enter house id</label>
                                <input id="house_id" name="house_id" value="'''+str(house['house_id'])+'''" class="input2"/><br>
                                <label for="telegram_users">Enter telegram chat_ids</label>
                                <input id="telegram_users" name="telegram_users" value="'''+tel_users.get("0")+'''" class="input2"/>
                                <input id="telegram_users2" name="telegram_users2" value="'''+tel_users.get("1")+'''" class="input2"/>
                                <input id="telegram_users3" name="telegram_users3" value="'''+tel_users.get("2")+'''" class="input2"/>
                                <input id="telegram_users4" name="telegram_users4" value="'''+tel_users.get("3")+'''" class="input2"/><br>
                                <label for="thingspeak_id">Enter thingspeak channel</label>
                                <input id="thingspeak_id" name="thingspeak_id" value="'''+str(house['thingspeak_channel_ID'])+'''" class="input2"/><br>
                                <label for="freeboard">Enter freeboard link</label>
                                <input id="freeboard" name="freeboard" value="'''+str(freeboard_link)+'''" class="input2"/><br>

                                <h4>Sensor list</h4>
                                <label for="sensor_0">Sensor: </label>
                                <input id="sensor_0" name="sensor_0" placeholder="sensor name" value="'''+sensors_list.get("0")+'''" class="input2"/><br>
                                <label for="sensor_1">Sensor: </label>
                                <input id="sensor_1" name="sensor_1" placeholder="sensor name" value="'''+sensors_list.get("1")+'''" class="input2"/><br>
                                <label for="sensor_2">Sensor: </label>
                                <input id="sensor_2" name="sensor_2" placeholder="sensor name" value="'''+sensors_list.get("2")+'''" class="input2"/><br>
                                <label for="sensor_3">Sensor: </label>
                                <input id="sensor_3" name="sensor_3" placeholder="sensor name" value="'''+sensors_list.get("3")+'''" class="input2"/><br>
                                <label for="sensor_4">Sensor: </label>
                                <input id="sensor_4" name="sensor_4" placeholder="sensor name" value="'''+sensors_list.get("4")+'''" class="input2"/><br>
                                <label for="sensor_5">Sensor: </label>
                                <input id="sensor_5" name="sensor_5" placeholder="sensor name" value="'''+sensors_list.get("5")+'''" class="input2"/><br>
                                <label for="sensor_6">Sensor: </label>
                                <input id="sensor_6" name="sensor_6" placeholder="sensor name" value="'''+sensors_list.get("6")+'''" class="input2"/><br>
                                <label for="sensor_7">Sensor: </label>
                                <input id="sensor_7" name="sensor_7" placeholder="sensor name" value="'''+sensors_list.get("7")+'''" class="input2"/><br>
                                <label for="sensor_8">Sensor: </label>
                                <input id="sensor_8" name="sensor_8" placeholder="sensor name" value="'''+sensors_list.get("8")+'''" class="input2"/><br>
                                <label for="sensor_9">Sensor: </label>
                                <input id="sensor_9" name="sensor_9" placeholder="sensor name" value="'''+sensors_list.get("9")+'''" class="input2"/><br><br>
                                <input type="submit" class="button1 button4"/>
                            </form>
                            <footer>
                            <p>All rights reserved ©</p>
                            </footer>
                            </div>
                        </body>
                        </html>'''
        elif params.get("modify_house"):
            sensors_dict = {}
            sensors_ids = ["010", "009", "008", "007", "006", "005", "004", "003", "002", "001"]
            for key in sorted(params.keys()):
                if key == "sensor_0" and params.get(key) != "":
                    sensors_dict.update({sensors_ids.pop(): {"sensor": str(params['sensor_0'])}})
                if key == "sensor_1" and params.get(key) != "":
                    sensors_dict.update({sensors_ids.pop(): {"sensor": str(params['sensor_1'])}})
                if key == "sensor_2" and params.get(key) != "":
                    sensors_dict.update({sensors_ids.pop(): {"sensor": str(params['sensor_2'])}})
                if key == "sensor_3" and params.get(key) != "":
                    sensors_dict.update({sensors_ids.pop(): {"sensor": str(params['sensor_3'])}})
                if key == "sensor_4" and params.get(key) != "":
                    sensors_dict.update({sensors_ids.pop(): {"sensor": str(params['sensor_4'])}})
                if key == "sensor_5" and params.get(key) != "":
                    sensors_dict.update({sensors_ids.pop(): {"sensor": str(params['sensor_5'])}})
                if key == "sensor_6" and params.get(key) != "":
                    sensors_dict.update({sensors_ids.pop(): {"sensor": str(params['sensor_6'])}})
                if key == "sensor_7" and params.get(key) != "":
                    sensors_dict.update({sensors_ids.pop(): {"sensor": str(params['sensor_7'])}})
                if key == "sensor_8" and params.get(key) != "":
                    sensors_dict.update({sensors_ids.pop(): {"sensor": str(params['sensor_8'])}})
                if key == "sensor_9" and params.get(key) != "":
                    sensors_dict.update({sensors_ids.pop(): {"sensor": str(params['sensor_9'])}})

            sensors = {"sensors": []}

            for item in sorted(sensors_dict.keys()):
                d = {"sensor_type": str(sensors_dict.get(item)['sensor']),
                     "sensor_id": str(params['house_id']) + str(item)}
                sensors['sensors'].append(d)

            tel_users = []
            if params.get("telegram_users") and str(params.get("telegram_users")) != "":
                tel_users.append(params["telegram_users"])
            if params.get("telegram_users2") and str(params.get("telegram_users2")) != "":
                tel_users.append(params["telegram_users2"])
            if params.get("telegram_users3") and str(params.get("telegram_users3")) != "":
                tel_users.append(params["telegram_users3"])
            if params.get("telegram_users4") and str(params.get("telegram_user4")) != "":
                tel_users.append(params["telegram_users4"])

            dict = {"house_name": str(params['house_name']), "local_pi_ip": str(params['local_pi_ip']),
                    "house_id": str(params['house_id']),
                    "telegram_users": tel_users,
                    "sensors": sensors['sensors'], "latest_sensor_id": sensors['sensors'][-1]['sensor_id'],
                    "thingspeak_channel_ID": str(params['thingspeak_id'])}

            # QUI INVIARE dict AL RESOURCE catalog VIA REQUEST
            # creare il metodo setHJSON
            data = "modifyHJSON4HID"
            try:
                data = "modifyHJSON4HID*"+str(params['house_id'])+"*"+json.dumps(dict)
                requests.post("http://192.168.1.71:8080", data=data)
            except:
                print("Error in fetching data from resource catalog:", data)
                pass

            #modify the local threshold file too
            # updating the new house also in the thresholds file

            #with open('cc_webservice_config.json', 'r') as json_data_file:
            #    obj = json.load(json_data_file)

            default_thres = {}
            #for house in obj['houses']:
            #    if house['house_id'] == params['house_id']:
            #        default_thres.update(house['thresholds'])
            #        obj['houses'].remove(house)
            #check if freeboard field is not empty
            #if params.get('freeboard'):
            #    modified_h  = {"telegram_users": tel_users, "freeboard": str(params['freeboard']),
            #                 "house_id": str(params['house_id']),
            #                 "thresholds": default_thres}
            #else:
            #    modified_h = {"telegram_users": tel_users, "freeboard": "",
            #                  "house_id": str(params['house_id']),
            #                  "thresholds": default_thres}

            #obj['houses'].append(modified_h)
            #with open('cc_webservice_config.json', 'w') as json_data_file:
            #    json.dump(obj, json_data_file)
            if params.get('freeboard'):
                modified_h  = {"telegram_users": tel_users, "freeboard": str(params['freeboard']),
                              "house_id": str(params['house_id'])}
            else:
                 modified_h = {"telegram_users": tel_users, "freeboard": "",
                               "house_id": str(params['house_id'])}

            data = "modifyHouseThresholds"
            try:
                data = "modifyHouseThresholds*" + str(params['house_id']) + "*" + json.dumps(modified_h)
                requests.post("http://192.168.1.72:8081", data=data)
            except:
                print("Error in fetching data from resource catalog:", data)
                pass

            return open("login_form.html")

    def PUT(self):
        return
    def DELETE(self):
        return

if __name__=="__main__":
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
            'server.socket_host': '0.0.0.0',
            'tools.staticdir.root': os.path.abspath(os.getcwd())
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'static'
            # 'tools.staticdir.index': './public/freeboard_old/index.html'
        }
    }
    cherrypy.tree.mount(RCWebService(), '/', conf)
    #cherrypy.server.socket_host = '192.168.1.72'
    #cherrypy.server.socket_port = 8080
    cherrypy.engine.start()
    cherrypy.engine.block()