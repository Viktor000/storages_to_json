from models.netapp import NetApp
from models.vnx import VNX
from models.netapp_e import NetAppE
from models.hitachi import Hitachi
from models.powerMax import PowerMax
from models.base.storage import Storage
import logging
import time
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool  
import os
import argparse
import re

logger = logging.getLogger(__name__)
start_time = time.time()

logging.basicConfig(level=logging.DEBUG, filename="py_log.log",filemode="w",
                    format="%(asctime)s %(levelname)s %(module)s - %(message)s")

netapp_e='./e_series/n5001_E5600_1RF13_08_1_inside.txt'
netapp_e='10.161.80.103'
storage_name='10.161.100.251'
ip='10.164.1.66'
user_emc=os.environ.get('USERNAME_EMC')
password_emc=os.environ.get('PASSWORD_EMC')
username=os.environ.get('USERNAME')
password=os.environ.get('PASSWORD')


def parseConfig():
    parser = argparse.ArgumentParser()
    parser.add_argument("-ip", "--ip_address", help="Storage address")
    parser.add_argument("-u", "--username", help="Storage username")
    parser.add_argument("-p", "--password", help="Storage password")
    parser.add_argument("-m", "--model", help="Storage model")
    parser.add_argument("-t", "--type", help="Storage access type")
    parser.add_argument("-e", "--elid", help="Storage Elid")
    args = parser.parse_args()
    return args

def job(device):
    if not device[6]:
        device[6]=f'{device[2]}_{device[0]}_{device[5]}'
    if device[1]=='NetApp'and ('AFF' in device[2] or 'FAS' in device[2]):
        dev= NetApp(device[0],device[1],device[2],device[3],device[4],device[5],device[6])
    if device[1]=='EMC' and 'VNX' in device[2]:
        dev= VNX(device[0],device[1],device[2],device[3],device[4],device[5],device[6])
    if device[1]=='NetApp' and 'E-series' in device[2]:
        dev= NetAppE(device[0],device[1],device[2],device[3],device[4],device[5],device[6])
    if device[1]=='Hitachi' and 'VSP' in device[2]:
        dev= Hitachi(device[0],device[1],device[2],device[3],device[4],device[5],device[6])
    if device[1]=='EMC' and 'PowerMax' in device[2]:
        dev= PowerMax(device[0],device[1],device[2],device[3],device[4],device[5],device[6])
        dev.testmode=True
    dev.collectData()
    dev.exportDataToFile()
    dev.report['time']=round(time.time() - start_time,2)
    print(dev.report)


if __name__ == '__main__':
    
    args=parseConfig()
    if args.ip_address:
        data=args.model.split(' ')
        vendor=data[0]
        model=' '.join(data[1:])
        device=[args.ip_address,vendor,model,args.type,args.username,args.password,args.elid]
        job(device)
    else:
        storage_list=[]
        device_list=[]
        device_list.append([storage_name,'EMC', 'VNX5600','CLI',user_emc,password_emc])
        # device_list.append([ip,'NetApp','AFF','API',username,password])
        # device_list.append([ip,'NetApp','FAS','CLI',username,password])
        #device_list.append([netapp_e,'NetApp','E-series','API',username,password])
        #device_list.append([netapp_e,'Hitachi','VSP F600','API',username,password])
        #device_list.append([netapp_e,'EMC','PowerMax 2000','API',username,password])
        pool = ThreadPool(8)
        result=pool.map(job,device_list)


    #print (f'Total time: {round(time.time() - start_time,2)} seconds')
