Project Cadrea


A brief project summary of the IoT project for Air quality control in a Smart Home




Performed By:


Deepan Anbarasan(S241446)
Dena Markudova (S239609)
Giampaolo Marinaro(S242195)
Raimondo Gallo(S251857)


 Summary:
 
This project aims to tackle the problem of indoor air pollution that’s ravaging many major cities in the world. The goal was to design a system that can maintain the indoor air quality of a house without compromising the comfort and safety of the user while being energy conscious. We have built a prototype keeping this goal in mind.
To attain the goals mentioned, the system collects pollution, climate data from inside the house and the external weather conditions along with checking for gas leaks. The system then decides based on this data if there some action it needs to do to reduce pollution or risks from gas leak. The system can do two possible solutions to reduce pollution – open windows or run an air purifier. The choice between the two depends on the comfort thresholds set by the user and the general conditions both inside and outside. In the case of a gas leak, the system also alerts the user via Telegram messaging app. The user’s presence is also detected and/or predicted to decide on whether to act immediately. There is also a vacation mode that can be set easily using Telegram, that helps to keep the system in a stand-by mode. The user can also visualize the status of the house easily using the freeboard dashboard where the most relevant information is represented concisely.  
The entire system is built using the Microservices architecture to make the system resilient and easy to update and up-scale. Configuration files are present for each module which makes changes and maintenance easy to handle. The communication protocols used are MQTT and REST. The hardware is a Raspberry pi connected to sensors and actuators through relay circuits. The idea is to have one Raspberry Pi for each house. Most modules except the Resource catalogue (RC) and Threshold service (TS) are specific to the room/house. The RC and TS are common to all rooms/houses.  






