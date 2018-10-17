# -*- coding: utf-8 -*-
import cherrypy
import os
import requests
import json
import mysql.connector as mc                                #Spariscono i campi nel form quando modifico e salvo i valori.
import sys
#Controllare gli indici dei dizionari tmp e params
#import lxml
#from bs4 import BeautifulSoup, Tag
try:
    with open('config_RC_WS.json', 'r') as json_data_file:
        obj = json.load(json_data_file)
        RC_address = obj['RC_base_url']
except:
    print("Error reading addresses file.")
    pass

port = 8081 #8081
url = '192.168.1.72' #192.168.1.72
cherrypy.config.update({'server.socket_port': port})
#cherrypy.config.update({'server.socket_host': url,
#                       'server.socket_port': port,
#                      })
flag = 0
online_id = 0
index_page = ""
telegram_users = []

def getTempHTML(dict):
    labels = []
    form = []
    if dict['thresholds'].has_key('temperature'):
        l = '''<b id="label_temp">''' + "Temperature: " + str(dict["thresholds"]["temperature"]) + '''</b><br>'''
        i = '''<label for="new_t_temp">Enter a value for Temperature range (e.g. 7 means +/-7):</label>
               <input id="new_t_temp" name="new_t_temp" class="input1 type="number" step="0.01" min="1" max="15" value="''' + str(
               dict["thresholds"]["temperature"]) + '''"/><br>'''
        form.append(i)
        labels.append(l)
    if dict['thresholds'].has_key('init_temp_high'):
        l = '''<b id="label_temp_high">''' + "Init High Temp threshold: " + str(
               dict["thresholds"]["init_temp_high"]) + '''</b><br>'''
        i = '''<label for="init_temp_high">Enter initial upper threshold for Temperature:</label>
               <input id="init_temp_high" name="init_temp_high" class="input1 type="number" step="0.01" min="10" max="35" value="''' + str(
               dict["thresholds"]["init_temp_high"]) + '''"/><br>'''
        form.append(i)
        labels.append(l)

    if dict['thresholds'].has_key('init_temp_low'):
        l = '''<b id="label_temp_low">''' + "Init Low Temp threshold: " + str(
               dict["thresholds"]["init_temp_low"]) + '''</b><br>'''
        i = '''<label for="init_temp_low">Enter initial lower threshold for Temperature:</label>
               <input id="init_temp_low" name="init_temp_low" class="input1 type="number" step="0.01" min="10" max="35" value="''' + str(
               dict["thresholds"]["init_temp_low"]) + '''"/><br>'''
        form.append(i)
        labels.append(l)
    return labels, form

def getHumidHTML(dict):
    labels = []
    form = []
    if dict['thresholds'].has_key('init_RH_high'):
        l = '''<b id="label_RH_high">''' + "Init High RH threshold: " + str(dict["thresholds"]["init_RH_high"]) + '''</b><br>'''
        i = '''<label for="init_RH_high">Enter initial upper threshold for Relative Humidity:</label>
               <input id="init_RH_high" name="init_RH_high" class="input1 type="number" step="0.01" min="10" max="80" value="''' + str(
               dict["thresholds"]["init_RH_high"]) + '''"/><br>'''
        labels.append(l)
        form.append(i)
    if dict['thresholds'].has_key('init_RH_low'):
        l = '''<b id="label_RH_low">''' + "Init Low RH threshold: " + str(dict["thresholds"]["init_RH_low"]) + '''</b><br>'''
        i = '''<label for="init_RH_low">Enter initial lower threshold for Relative Humidity:</label>
               <input id="init_RH_low" name="init_RH_low" class="input1 type="number" step="0.01" min="10" max="80" value="''' + str(
               dict["thresholds"]["init_RH_low"]) + '''"/><br>'''
        labels.append(l)
        form.append(i)
    return labels, form


def getDustHTML(dict):
    labels = []
    form = []
    if dict['thresholds'].has_key('dust_in'):
        l = ''' <b id="label_indust">''' + "Inside dust: " + str(dict["thresholds"]["dust_in"]) + '''</b><br>'''
        i = '''<label for="new_t_indust">Enter new inside dust threshold:</label>
               <input id="new_t_indust" name="new_t_indust" class="input1 type="number" value="''' + str(
               dict["thresholds"]["dust_in"]) + '''"/><br>'''
        labels.append(l)
        form.append(i)
    if dict['thresholds'].has_key('dust_out'):
        l = '''<b id="label_oudust">''' + "Outside dust: " + str(dict["thresholds"]["dust_out"]) + '''</b><br>'''
        i = '''<label for="new_t_outdust">Enter new outside dust threshold:</label>
               <input id="new_t_outdust" name="new_t_outdust" class="input1 type="number" value="''' + str(
               dict["thresholds"]["dust_out"]) + '''"/><br>'''
        labels.append(l)
        form.append(i)
    return labels, form


def getGasHTML(dict):
    labels = []
    form = []
    if dict['thresholds'].has_key('gas'):
        l = '''<b id="label_gas">''' + "Gas: " + str(dict["thresholds"]["gas"]) + '''</b><br>'''
        i = '''<label for="new_t_gas">Enter new gas threshold:</label>
               <input id="new_t_gas" name="new_t_gas" class="input1 type="number" value="''' + str(
               dict["thresholds"]["gas"]) + '''"/><br><br>'''
        labels.append(l)
        form.append(i)
    return labels, form

def creatHTML(dict):
    t_labels, t_form = getTempHTML(dict)
    h_labels, h_form = getHumidHTML(dict)
    d_labels, d_form = getDustHTML(dict)
    g_labels, g_form = getGasHTML(dict)
    freeboard = dict['freeboard']

    page = ""
    page = '''<!DOCTYPE html><html lang="en"><head>
              <meta charset="UTF-8"><link rel="stylesheet" href="/static/style.css">
              <title>HomePage</title></head><body><div id="wrapper"><div id="banner"></div>
	          <div id="container"><div id = "left"><h1>Cadrea: Welcome home!</h1><p id="current_thresholds">
              <b id="house_id">'''+ "House ID: " + str(dict['house_id']) + '''</b><br>'''
    for label in t_labels: #add temperature labels
        page = page + label
    for label in h_labels:  # add humidity labels
        page = page + label
    for label in d_labels:  # add dust labels
        page = page + label
    for label in g_labels:  # add gas labels
        page = page + label

    page = page + '''</p><form method="post">'''

    for input in t_form: #add temperature inputs
        page = page + input
    for input in h_form:  # add humidity inputs
        page = page + input
    for input in d_form:  # add dust inputs
        page = page + input
    for input in g_form:  # add gas inputs
        page = page + input
    #onclick="location.href='http://192.168.1.72:3032/login.html'
    page = page + '''<input type="submit" class="button1 button4"/></form><br> </br>
	 </div><div id = "right"><p id="useful_links"><h3>Useful links</h3>
                     <input id="freeboard" type="button" class="button1 button4" onclick="location.href='''+"'"+str(freeboard)+"'"+'''"; value="Go to Freeboard" />
                     </p><br> </br><p>
		<h3>Logout</h3>
		<button class="button1 button4" onclick="location.href='http://'''+str(url)+''':'''+str(port)+'''/login.html';">Logout</button><br>
		</p></div></div><footer>
        <p>All rights reserved ©</p>
        </footer></div> </body></html>'''
    return page

def creatHTML2(dict, drop_down_list):
    t_labels, t_form = getTempHTML(dict)
    h_labels, h_form = getHumidHTML(dict)
    d_labels, d_form = getDustHTML(dict)
    g_labels, g_form = getGasHTML(dict)
    page = ""
    page = '''<!DOCTYPE html><html lang="en"><head><link rel="stylesheet" type="text/css" href="/static/style.css" />
              <meta charset="UTF-8"><link rel="stylesheet" href="style.css">
              <title>HomePage</title><script src="/static/show_data3.js" language="javascript" type="text/javascript"></script>
              <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.2.1/jquery.min.static"></script></head><body><div id="wrapper">
              <div id="banner"></div><div id="container"><div id = "left">
              <?phpinclude "/static/phpGet.php";?><h1>Cadrea: Welcome home!</h1><p id="current_thresholds">
              <b id="house_id">'''+ "House ID: " + str(dict['house_id']) + '''</b><br>'''
    for label in t_labels: #add temperature labels
        page = page + label
    for label in h_labels:  # add humidity labels
        page = page + label
    for label in d_labels:  # add dust labels
        page = page + label
    for label in g_labels:  # add gas labels
        page = page + label
    #aggiungere una label descrittiva per la drop down list
    '''<script type="text/javascript">$("#house_id_list").change(function() {
                             alert("ciao");
                var url = "http://127.0.0.1:3030/"; var house = $("#house_id_list:selected" ).text(); var URL = url + house;
                $.get("http://127.0.0.1:3030/001", function(data){ alert("Data: " + data);});
                });</script>'''                         #http://127.0.0.1:
    page = page + '''</p><form method="post"><label>Pick a house: </label>
			   <div class="dropdown">'''+drop_down_list+'''</div><br><br>'''

    for input in t_form: #add temperature inputs
        page = page + input
    for input in h_form:  # add humidity inputs
        page = page + input
    for input in d_form:  # add dust inputs
        page = page + input
    for input in g_form:  # add gas inputs
        page = page + input

    page = page + '''<input type="submit" class="button1 button4"/></form><br> </br>
	                 </div><div id = "right"><p id="useful_links"><h3>Useful links</h3></p><br> </br>
		<p><h3>Logout</h3><button class="button1 button4" onclick="location.href='http://'''+str(url)+''':'''+str(port)+'''/login.html';">Logout
		</button><br></p></div></div><footer><p>All rights reserved ©</p></footer></div> </body></html>'''
    return page

class WebServer(object):

    exposed = True

    def GET(self, *uri,**params):
        global flag
        global flag_admin
        flag_admin = False
        with open('cc_webservice_config.json', 'r') as json_data_file:
            obj = json.load(json_data_file)

        if(uri[0] == "login.html"):
            return open("login_form.html")

        if(len(uri) == 2):
            if (uri[1] == "tempRange"):
                for house in obj['houses']:
                    if house['house_id'] == uri[0]:
                        return (str(house["thresholds"]["temperature"]))
                return "-1"
            elif (uri[1] == "init_temp_low"):
                for house in obj['houses']:
                    if house['house_id'] == uri[0]:
                        return (str(house["thresholds"]["init_temp_low"]))
                return "-1"
            elif (uri[1] == "init_temp_high"):
                for house in obj['houses']:
                    if house['house_id'] == uri[0]:
                        return (str(house["thresholds"]["init_temp_high"]))
                return "-1"
            elif (uri[1] == "init_RH_low"):
                for house in obj['houses']:
                    if house['house_id'] == uri[0]:
                        return (str(house["thresholds"]["init_RH_low"]))
                return "-1"
            elif (uri[1] == "init_RH_high"):
                for house in obj['houses']:
                    if house['house_id'] == uri[0]:
                        return (str(house["thresholds"]["init_RH_high"]))
                return "-1"
            elif (uri[1] == "dust_in"):
                for house in obj['houses']:
                    if house['house_id'] == uri[0]:
                        return (str(house["thresholds"]["dust_in"]))
                return "-1"
            elif (uri[1] == "dust_out"):
                for house in obj['houses']:
                    if house['house_id'] == uri[0]:
                        return (str(house["thresholds"]["dust_out"]))
                return "-1"
            elif (uri[1] == "gas"):
                for house in obj['houses']:
                    if house['house_id'] == str(uri[0]):
                        return (str(house["thresholds"]["gas"]))
                return "-1"
            else: return "-1"
        else: "-1"


    def POST(self, *uri, **params):
        global flag
        global online_id
        global index_page
        global telegram_users
        global flag_admin
        index_page = ""
        h_id = 0
        telegram_users = []
        tmp = {}
        my_string = cherrypy.request.body.read()

        #------------------------
        if "getThreshObj" in my_string:
            print ""

        #------------------------

        if "getDBItems" in my_string:
            DB_username = ""
            DB_password = ""
            DB_name = ""
            DB_host = ""
            try:
                with open('config_RC_WS.json', 'r') as json_data_file:
                    obj = json.load(json_data_file)
                    DB_username = obj['DB_username']
                    DB_password = obj['DB_password']
                    DB_name = obj['DB_name']
                    DB_host = obj['DB_host']
            except:
                print("Error reading DB addresses from file.")
                pass
            try:
                connection = mc.connect(user=DB_username,
                                        password=DB_password,
                                        host=DB_host,
                                        database=DB_name)
            except mc.Error as e:
                print("Error %d: %s" % (e.args[0], e.args[1]))
                sys.exit(1)

            cursor = connection.cursor()
            cursor.execute("SELECT loginid, username, password, house_id FROM login")
            dict = {'ids': []}

            for (loginid, username, password, house_id) in cursor:
                dict['ids'].append({'loginid': str(loginid), 'username': str(username), 'password': str(password),
                                    'house_id': str(house_id)})
            cursor.close()
            connection.close()
            return json.dumps(dict)

        elif "setDBnewItem" in my_string: #create a new item in the database
            DB_username = ""
            DB_password = ""
            DB_name = ""
            DB_host = ""
            try:
                with open('config_RC_WS.json', 'r') as json_data_file:
                    obj = json.load(json_data_file)
                    DB_username = obj['DB_username']
                    DB_password = obj['DB_password']
                    DB_name = obj['DB_name']
                    DB_host = obj['DB_host']
            except:
                print("Error reading DB addresses from file.")
                pass

            command, user_name, pass_word, email, house_id  = my_string.split(":")
            try:
                connection = mc.connect(user=DB_username,
                                        password=DB_password,
                                        host=DB_host,
                                        database=DB_name)
            except mc.Error as e:
                print("Error %d: %s" % (e.args[0], e.args[1]))
                sys.exit(1)

            cursor = connection.cursor()
            add_user = ("INSERT INTO login "
                        "(username, password, email, house_id) "
                        "VALUES (%s, %s, %s, %s)")
            data_user = (user_name, pass_word, email, house_id)

            #cursor.execute(add_user, data_user)
            #connection.commit()
            cursor.close()
            connection.close()

        elif not params.has_key("username"):
            if not flag_admin:
                with open('cc_webservice_config.json', 'r') as json_data_file:
                     obj = json.load(json_data_file)
                for item in obj['houses']:
                    if str(item['house_id']) == str(online_id):
                        if len(item['telegram_users']) != 0:
                            telegram_users.extend(item['telegram_users'])
                            tmp = {'freeboard':str(item['freeboard']),'house_id': str(online_id), 'telegram_users': telegram_users, 'thresholds': {}}
                        else: tmp = {'freeboard':str(item['freeboard']),'house_id':str(online_id),'telegram_users':[],'thresholds':{}}

                #if len(telegram_users) == 0:
                #    tmp = {'house_id':str(online_id),'telegram_users':[],'thresholds':{}}
                #else: tmp = {'house_id':str(online_id),'telegram_users':telegram_users,'thresholds':{}}

                if params.get('new_t_temp'):
                    tmp['thresholds']['temperature'] = float(params['new_t_temp'])
                if params.get('init_temp_low'):
                    tmp['thresholds']['init_temp_low'] = float(params['init_temp_low'])
                if params.get('init_temp_high'):
                    tmp['thresholds']['init_temp_high'] = float(params['init_temp_high'])
                if params.get('init_RH_high'):
                    tmp['thresholds']['init_RH_high'] = float(params['init_RH_high'])
                if params.get('init_RH_low'):
                    tmp['thresholds']['init_RH_low'] = float(params['init_RH_low'])
                if params.get('new_t_indust'):
                    tmp['thresholds']['dust_in'] = float(params['new_t_indust'])
                if params.get('new_t_outdust'):
                    tmp['thresholds']['dust_out'] = float(params['new_t_outdust'])
                if params.get('new_t_gas'):
                    tmp['thresholds']['gas'] = float(params['new_t_gas'])

                for item in obj['houses']:
                    if str(item['house_id']) == str(tmp['house_id']):
                        obj['houses'].remove(item)

                obj['houses'].append(tmp)
                with open('cc_webservice_config.json', 'w') as json_data_file:
                    json.dump(obj, json_data_file)

                page = creatHTML(tmp)
                return page

            else:
                online_dict = {}
                with open('cc_webservice_config.json', 'r') as json_data_file:
                     obj = json.load(json_data_file)
                for house in obj['houses']:
                    if str(house['house_id']) == str(params['house_id_list']):
                        online_dict.update(house)
                        if len(house['telegram_users']) != 0:
                            telegram_users.extend(house['telegram_users'])
                            tmp = {'freeboard':str(house['freeboard']),'house_id': str(house['house_id']), 'telegram_users': telegram_users, 'thresholds': {}}
                        else: tmp = {'freeboard':str(house['freeboard']),'house_id':str(house['house_id']),'telegram_users':[],'thresholds':{}}

                #if len(telegram_users) == 0:
                #    tmp = {'house_id':str(online_id),'telegram_users':[],'thresholds':{}}
                #else: tmp = {'house_id':str(online_id),'telegram_users':telegram_users,'thresholds':{}}

                if params.get('new_t_temp') and online_dict['thresholds'].has_key('temperature'):
                    tmp['thresholds']['temperature'] = float(params['new_t_temp'])
                if params.get('init_temp_low') and online_dict['thresholds'].has_key('init_temp_low'):
                    tmp['thresholds']['init_temp_low'] = float(params['init_temp_low'])
                if params.get('init_temp_high') and online_dict['thresholds'].has_key('init_temp_high'):
                    tmp['thresholds']['init_temp_high'] = float(params['init_temp_high'])
                if params.get('init_RH_high') and online_dict['thresholds'].has_key('init_RH_high'):
                    tmp['thresholds']['init_RH_high'] = float(params['init_RH_high'])
                if params.get('init_RH_low') and online_dict['thresholds'].has_key('init_RH_low'):
                    tmp['thresholds']['init_RH_low'] = float(params['init_RH_low'])
                if params.get('new_t_indust') and online_dict['thresholds'].has_key('dust_in'):
                    tmp['thresholds']['dust_in'] = float(params['new_t_indust'])
                if params.get('new_t_outdust') and online_dict['thresholds'].has_key('dust_out'):
                    tmp['thresholds']['dust_out'] = float(params['new_t_outdust'])
                if params.get('new_t_gas') and online_dict['thresholds'].has_key('gas'):
                    tmp['thresholds']['gas'] = float(params['new_t_gas'])

                dict = {}
                for house in obj['houses']:
                    if house['house_id'] == str(params['house_id_list']):
                        obj['houses'].remove(house)
                dict.update(tmp)

                obj['houses'].append(tmp)
                with open('cc_webservice_config.json', 'w') as json_data_file:
                    json.dump(obj, json_data_file)
                                                                                                            #showFields()
                drop_down_list = "<select name='house_id_list' id='house_id_list' class='dropbtn' onchange='phpGet()';><div class='dropdown-content'>"
                for house in obj['houses']:
                    if house['house_id'] == str(params['house_id_list']):
                        drop_down_list = drop_down_list + "<option value='" + str(house['house_id']) + "' selected>" + str(
                                house['house_id']) + "</option>"
                    else:
                        drop_down_list = drop_down_list + "<option value='" + str(house['house_id']) + "'>" + str(
                            house['house_id']) + "</option>"
                drop_down_list = drop_down_list + "</div></select>"

                page = creatHTML2(dict, drop_down_list)
                return page

        else:
            flag = 0
            flag_admin = False
            try:
                connection = mc.connect(user='root',
                                        password='',
                                        host='localhost',
                                        database='login')
            except mc.Error as e:
                print("Error %d: %s" % (e.args[0], e.args[1]))
                sys.exit(1)

            cursor = connection.cursor()
            cursor.execute("SELECT loginid, username, password, house_id FROM login")
            dict = {'ids':[]}

            for (loginid, username, password, house_id) in cursor:
                dict['ids'].append({'loginid':str(loginid), 'username':str(username), 'password':str(password), 'house_id':str(house_id)})
            cursor.close()
            connection.close()

            for item in dict['ids']:
                if flag == 0 and str(params['username']) == str(item['username']) and str(params['password']) == str(item['password']):
                    flag = 1
                    h_id = item['house_id'] #house the authenticated user belongs to
                    online_id = h_id
                    if str(params['username']) == "admin" and str(params['password']) == "passadmin": #o con item['house_id']=="default"
                        flag_admin = True

            if flag == 1:
                if flag_admin:
                    drop_down_list = "<select name='house_id_list' id='house_id_list' class='dropbtn' onchange='phpGet()';><div class='dropdown-content'>"
                    default_dict = {}
                    with open('cc_webservice_config.json', 'r') as json_data_file:
                        obj = json.load(json_data_file)
                    for house in obj['houses']:
                        if not (house['house_id'] == "default"):
                            drop_down_list = drop_down_list + "<option value='" + str(house['house_id']) + "'>" + str(
                                house['house_id']) + "</option>"
                        else:
                            drop_down_list = drop_down_list + "<option value='" + str(house['house_id']) + "' selected>" + str(
                                house['house_id']) + "</option>"
                            default_dict.update(house)
                    drop_down_list = drop_down_list + "</div></select>"

                    page = creatHTML2(default_dict, drop_down_list)
                    return page

                else:
                    dict2 = {}
                    found = 0
                    with open('cc_webservice_config.json', 'r') as json_data_file:
                         obj = json.load(json_data_file)
                    for item in obj['houses']:
                        if found != 1 and str(item['house_id']) == str(h_id):
                            found = 1
                            dict2.update(item)

                    page = creatHTML(dict2) #"House ID: " + str(online_id)
                    return page

            else:
                return open("login_form.html")
        return

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
    cherrypy.tree.mount(WebServer(), '/', conf)
    #cherrypy.server.socket_host = '192.168.1.72'
    #cherrypy.server.socket_port = 8081
    cherrypy.engine.start()
    cherrypy.engine.block()