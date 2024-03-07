from models.netapp import NetApp
from models.vnx import VNX
from models.netapp_e import NetAppE
from models.base.storage import Storage
import logging
import time
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool  
import os

logger = logging.getLogger(__name__)
start_time = time.time()

logging.basicConfig(level=logging.DEBUG, filename="py_log.log",filemode="w",
                    format="%(asctime)s %(levelname)s %(module)s - %(message)s")

netapp_e='./e_series/n5001_E5600_1RF13_08_1_inside.txt'
storage_name='10.161.100.251'
ip='10.164.1.66'
user_emc=os.environ.get('USERNAME_EMC')
password_emc=os.environ.get('PASSWORD_EMC')
username=os.environ.get('USERNAME')
password=os.environ.get('PASSWORD')


def job(device):
    if device[1]=='NetApp'and ('AFF' in device[2] or 'FAS' in device[2]):
        dev= NetApp(device[0],device[1],device[2],device[3],device[4],device[5])
    if device[1]=='EMC' and 'VNX' in device[2]:
        dev= VNX(device[0],device[1],device[2],device[3],device[4],device[5])
    if device[1]=='NetApp' and 'E-series' in device[2]:
        dev= NetAppE(device[0],device[1],device[2],device[3],device[4],device[5])
    dev.collectData()
    dev.exportDataToFile()


if __name__ == '__main__':
    storage_list=[]
    device_list=[]
    device_list.append([storage_name,'EMC', 'VNX5600','CLI',user_emc,password_emc])
    #device_list.append([ip,'NetApp','AFF','API',username,password])
    #device_list.append([ip,'NetApp','FAS','CLI',username,password])
    # device_list.append([netapp_e,'NetApp','E-series','CLI_file',username,password])
    
    pool = ThreadPool(8)
    result=pool.map(job,device_list)


    print (f'Total time: {round(time.time() - start_time,2)} seconds')
