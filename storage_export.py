from models.netapp import NetApp
from models.vnx import VNX
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

storage_name='10.161.100.251'

ip='10.164.1.66'
username=os.environ.get('USERNAME')
password=os.environ.get('PASSWORD')

# dev =NetApp(ip,'NetApp','AFF','CLI',username,password)
# a=dev.__get_controllers_CLI__()
# #dev.collectData()
# #print (dev.exportData())

# #print(dev.__get_disks_CLI__())
# print(a)


#exit()

def job(device):
    if device[1]=='NetApp':
        dev= NetApp(device[0],device[1],device[2],device[3],device[4],device[5])
    if device[1]=='EMC' and 'VNX' in device[2]:
        dev= VNX(device[0],device[1],device[2],device[3])
    dev.collectData()
    dev.exportDataToFile()


if __name__ == '__main__':
    storage_list=[]
    device_list=[]
    device_list.append([storage_name,'EMC', 'VNX5600','CLI'])
    device_list.append([ip,'NetApp','AFF','API',username,password])
    device_list.append([ip,'NetApp','AFF','CLI',username,password])
    

    pool = ThreadPool(3)
    result=pool.map(job,device_list)


    print (f'Total time: {round(time.time() - start_time,2)} seconds')
