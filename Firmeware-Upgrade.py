from time import time
import sys
import ipaddress

import threading
from multiprocessing.dummy import Pool as ThreadPool

import csv

from netmiko import ConnectHandler
from getpass import getpass
from netmiko.ssh_exception import NetMikoTimeoutException
from paramiko.ssh_exception import SSHException
from netmiko.ssh_exception import AuthenticationException

#------------------------------------------------------------------------------
def config_worker( CONFIG_PARAMS_LIST):
    IP_ADDRESS_DEVICE = CONFIG_PARAMS_LIST [0]
    USERNAME = CONFIG_PARAMS_LIST [1]
    PASSWORD = CONFIG_PARAMS_LIST [2]
    FIRMEWARE_LIST = CONFIG_PARAMS_LIST [3]
    SCP_IP = CONFIG_PARAMS_LIST [4]
    SCP_USERNAME = CONFIG_PARAMS_LIST [5]
    SCP_PASSWORD = CONFIG_PARAMS_LIST [6]

    ios_devices = {
        "device_type": "cisco_ios",
        "ip": IP_ADDRESS_DEVICE,
        "username": USERNAME,
        "password": PASSWORD
    }
    for i in range (1,2):
        try:
            net_connect = ConnectHandler(**ios_devices)
        except (AuthenticationException):
            print ("**** Error: Authentication failure: " + IP_ADDRESS_DEVICE + " ****")
            continue
        except (NetMikoTimeoutException):
            print ("**** Error: Timeout to device: " + IP_ADDRESS_DEVICE + " ****")
            continue
        except (EOFError):
            print ("**** Error: End of file while attempting device: " + IP_ADDRESS_DEVICE + " ****")
            continue
        except (SSHException):
            print ("**** Error: SSH Issue. Are you sure SSH is enabled?:  " + IP_ADDRESS_DEVICE + " ****")
            continue
        except Exception as unknown_error:
            print ("**** Error: Some other error " + IP_ADDRESS_DEVICE + " ****")
            continue

        LIST_VESION_ALL = []
        for VERSION_IN_LIST in range (len(FIRMEWARE_LIST)):
            LIST_VESION_ALL.append(FIRMEWARE_LIST[VERSION_IN_LIST][1])

        LIST_VERSION_ROUTER = []
        for VERSION_IN_LIST_ROUTER in range (len(FIRMEWARE_LIST)):
            if "Router" == (FIRMEWARE_LIST[VERSION_IN_LIST_ROUTER][0]):
                LIST_VERSION_ROUTER.append(FIRMEWARE_LIST[VERSION_IN_LIST_ROUTER][1])

        LIST_VERSION_SWITCH = []
        for VERSION_IN_LIST_SWITCH in range (len(FIRMEWARE_LIST)):
            if "Switch" == (FIRMEWARE_LIST[VERSION_IN_LIST_SWITCH][0]):
                LIST_VERSION_SWITCH.append(FIRMEWARE_LIST[VERSION_IN_LIST_SWITCH][1])

        output_version = net_connect.send_command("show version")
        net_connect.disconnect()
        for SOFTWARE_VERSION in LIST_VESION_ALL:
            inter_version = 0
            inter_version = output_version.find(SOFTWARE_VERSION)
            if inter_version > 0:
                UPLOAD_FILE = 0
                if SOFTWARE_VERSION in LIST_VERSION_SWITCH:
                    UPLOAD_FILE = FIRMEWARE_VERSION_FOR_UPLOAD(SOFTWARE_VERSION,FIRMEWARE_LIST)
                    print (IP_ADDRESS_DEVICE + " Switch Software version found: " + SOFTWARE_VERSION + " Upload: " + UPLOAD_FILE)
                    SCP_UPLOAD(IP_ADDRESS_DEVICE, USERNAME, PASSWORD, UPLOAD_FILE, SCP_IP, SCP_USERNAME, SCP_PASSWORD, FIRMEWARE_UPLOAD_FILE_SYSTEM(SOFTWARE_VERSION, FIRMEWARE_LIST))
                    break


                elif SOFTWARE_VERSION in LIST_VERSION_ROUTER:
                    UPLOAD_FILE = FIRMEWARE_VERSION_FOR_UPLOAD(SOFTWARE_VERSION,FIRMEWARE_LIST)
                    print (IP_ADDRESS_DEVICE + " Router Software version found: " + SOFTWARE_VERSION + " Upload: " + UPLOAD_FILE)
                    SCP_UPLOAD(IP_ADDRESS_DEVICE, USERNAME, PASSWORD, UPLOAD_FILE, SCP_IP, SCP_USERNAME, SCP_PASSWORD, FIRMEWARE_UPLOAD_FILE_SYSTEM(SOFTWARE_VERSION, FIRMEWARE_LIST))
                    break
    return

#------------------------------------------------------------------------------
def FIRMEWARE_VERSION_FOR_UPLOAD( SOFTWARE_VERSION,FIRMEWARE_LIST):
    for I in range (len(FIRMEWARE_LIST)):
        if SOFTWARE_VERSION == (FIRMEWARE_LIST[I][1]):
            VERSION_UPLOAD = (FIRMEWARE_LIST[I][2])
    return VERSION_UPLOAD


#------------------------------------------------------------------------------
def FIRMEWARE_UPLOAD_FILE_SYSTEM( SOFTWARE_VERSION,FIRMEWARE_LIST):
    for I in range (len(FIRMEWARE_LIST)):
        if SOFTWARE_VERSION == (FIRMEWARE_LIST[I][1]):
            FIRMEWARE_UPLOAD_FILE_SYSTEM = (FIRMEWARE_LIST[I][3])
    return FIRMEWARE_UPLOAD_FILE_SYSTEM

#------------------------------------------------------------------------------
def SCP_UPLOAD(IP_ADDRESS_DEVICE, USERNAME, PASSWORD, UPLOAD_FILE, SCP_IP, SCP_USERNAME, SCP_PASSWORD, FIRMEWARE_UPLOAD_FILE_SYSTEM):
    ios_devices = {
        "device_type": "cisco_ios",
        "ip": IP_ADDRESS_DEVICE,
        "username": USERNAME,
        "password": PASSWORD
    }
    for i in range (1,2):
        try:
            net_connect = ConnectHandler(**ios_devices)
        except (AuthenticationException):
            print ("**** Error: Authentication failure: " + IP_ADDRESS_DEVICE + " ****")
            continue
        except (NetMikoTimeoutException):
            print ("**** Error: Timeout to device: " + IP_ADDRESS_DEVICE + " ****")
            continue
        except (EOFError):
            print ("**** Error: End of file while attempting device: " + IP_ADDRESS_DEVICE + " ****")
            continue
        except (SSHException):
            print ("**** Error: SSH Issue. Are you sure SSH is enabled?:  " + IP_ADDRESS_DEVICE + " ****")
            continue
        except Exception as unknown_error:
            print ("**** Error: Some other error " + IP_ADDRESS_DEVICE + " ****")
            continue

        output_dir = net_connect.send_command("dir")
        int_dir = 0
        int_dir = output_dir.find(UPLOAD_FILE)
        if int_dir < 0:
            net_connect.send_config_set("file prompt quiet")
            COMMAND_SCP_UPLOAD = ("copy scp://" + SCP_USERNAME + ":" + SCP_PASSWORD + "@" + SCP_IP + "/" + UPLOAD_FILE + " " + FIRMEWARE_UPLOAD_FILE_SYSTEM + UPLOAD_FILE)
            print (IP_ADDRESS_DEVICE + " " +COMMAND_SCP_UPLOAD)
            net_connect.send_command(COMMAND_SCP_UPLOAD)
            net_connect.send_config_set("no file prompt quiet")
        else:
            print (IP_ADDRESS_DEVICE + " File exist, no upload")
            break
        output_dir = net_connect.send_command("dir")
        int_dir = 0
        int_dir = output_dir.find(UPLOAD_FILE)
        if int_dir > 0:
            print (IP_ADDRESS_DEVICE + " File sucesfully uploaded")
        else:
            print ("**** Error: Upload  " + IP_ADDRESS_DEVICE + " ****")
    net_connect.disconnect()
    return

#==============================================================================
# ---- Main: Get Configuration
#==============================================================================
print ("automatic firmware upgrade  \n this tool connects to network components and carries out a firmware upgrade; the restart must be carried out manuall")

try:
    with open('Firmeware.csv', newline='') as FIRMEWARE_LIST_FILE:
        reader = csv.reader(FIRMEWARE_LIST_FILE)
        FIRMEWARE_LIST = list(reader)
except:
    print("**** Error: can't open Firmeware-file (Firmeware.csv) ****")
    sys.exit()

USERNAME = input("Enter your SSH-Username (cisco): ") or "cisco"
PASSWORD = getpass("Enter your SSH-Password (cisco): ") or "cisco"

SCP_IP = input("Enter your SCP-IP (192.168.207.160): ") or "192.168.207.160"
SCP_USERNAME = input("Enter your SCP-Username (cisco): ") or "cisco"
SCP_PASSWORD = getpass("Enter your SCP-Password (cisco): ") or "cisco"

#read IP-address-list, any seperator possible
IP_ADDRESS_CSV_FILE = input ("Input CSV filename (ip-device.csv) :  ") or "ip-device.csv"
SPLIT = input ("seperator (,): ") or ","
try:
    IP_ADDRESS_CSV=open(IP_ADDRESS_CSV_FILE)
except:
    print("**** Error: can't open IP-address-file ****")
    sys.exit()
IP_ADDRESS_LIST_RAW = IP_ADDRESS_CSV.read()
IP_ADDRESS_CSV.close()
#format list
IP_ADDRESS_LIST_LINE = IP_ADDRESS_LIST_RAW.split(chr(10))
IP_ADDRESS_LIST = []
for LINE in IP_ADDRESS_LIST_LINE:
    if LINE:
        IP_ADDRESS_LIST.append(LINE.split(SPLIT))
print(IP_ADDRESS_LIST[0])
#take the right column
try:
    IP_ADDRESS_COLUMN = int(input("Column with IP-address (3): ") or "3")
except:
    print("**** Error: Input-type ****")
    sys.exit()
try:
    THREAD_NUMBER = int(input("How many Threas parallel (3): ") or "3")
except:
    print("**** Error: Input-type ****")
    sys.exit()
print ("")
#Technicians start counting at 1, computer scientists at 0
IP_ADDRESS_COLUMN = IP_ADDRESS_COLUMN - 1
#take the ip-address and start threads

#Threadpool config
CONFIG_PARAMS_LIST = []
threads = ThreadPool( THREAD_NUMBER )

#Start Action
starting_time = time()
try:
    for row in IP_ADDRESS_LIST:
        IP_ADDRESS = str.strip(str(row[IP_ADDRESS_COLUMN]))
        try:
            print ('Creating thread for:', ipaddress.ip_address(IP_ADDRESS))
            CONFIG_PARAMS_LIST.append( ( IP_ADDRESS, USERNAME, PASSWORD, FIRMEWARE_LIST, SCP_IP, SCP_USERNAME, SCP_PASSWORD ) )

        except:
            print ("**** Error: no IP-address: " + IP_ADDRESS + " ****")
except:
    print ("**** Error: seperator ****")

print ("\n--- Creating threadpool and launching ----\n")
results = threads.map( config_worker, CONFIG_PARAMS_LIST)

threads.close()
threads.join()

print ("\n---- End threadpool, elapsed time= " + str(round(time()-starting_time)) + "sec ----")
