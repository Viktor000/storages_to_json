import logging
import re

from models.base.storage import Storage
from models.base.drive import Drive
from models.base.lun import Lun
from models.base.volume import Volume
from models.base.network import Network
from models.base.shelf import Shelf
from models.base.psu import Psu
from models.base.controller import Controller

from requests.auth import HTTPBasicAuth
import requests
from requests.packages import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)


class PowerMax(Storage):
    def __init__(self, address, vendor, model,access_type,username,password,json_file_path='./'):
        super().__init__(address, vendor, model,access_type,json_file_path)
        self.username=username
        self.password=password
        self.fwVersion=''
        if access_type=='API':
            self.testmode=False
            self.headers={}
            self.basic = HTTPBasicAuth(self.username,self.password)
            self.auth=f'http://{self.address}:8443/'
            self.connect_args=f'http://{self.address}:8443/univmax/restapi/91/system/symmetrix'
            self.connect_args2=f'http://{self.address}:8443/univmax/restapi/91/sloprovisioning/symmetrix'
            try:
                #print(self.auth)
                response = requests.post(self.auth,verify=False,headers=self.headers,auth=self.basic)
                #print(response.json())
                self.token=response.json()['token']
                self.headers={'Authorization':f'Session {self.token}'}
            except Exception as e:
                #print('------------------------------------')
                print(e)    
                
            try:
                response = requests.get(self.connect_args,verify=False,headers=self.headers)
                data=response.json()['symmetrixId']
                #print('=========',response.json())
                for dev in data:
                    #print(dev)
                    #if dev['svpIp']==self.address:
                    self.storageId=dev
                    self.connect_args=f'{self.connect_args}/{self.storageId}'
            except Exception as e:
                print(e) 
                
    def __get_data_API__(self,url):
        try:
            response = requests.get(url,verify=False,headers=self.headers)
            # print(url)
            # print(response)
            return(response.json())
        except Exception as e:
            print(e)
    def __get_disks_API__(self):
        url=f'{self.connect_args}/disk'
        drives=self.__get_data_API__(url)['disk_ids']
        drive_list={}
        for drv in drives:
            if self.testmode and drv not in ('0','1','100A'):
                continue
            drv_data=self.__get_disk_API__(drv)
            disk=Drive(
                slot=drv_data['spindle_id'],
                vendor=drv_data['vendor'],
                model=drv_data['type'],
                size=drv_data['capacity']
            )
            disk_info=disk.exportData()
            if disk_info:
                drive_list[disk_info['slot']]=disk_info
        #print(drive_list)
        return drive_list
                
    
    def __get_disk_API__(self,drv):
        url=f'{self.connect_args}/disk/{drv}'
        return self.__get_data_API__(url)
    
    def __get_volumes_API__(self):
        url=f'{self.connect_args2}/{self.storageId}/volume'
        volumes=self.__get_data_API__(url)['resultList']['result']
        volume_list={}
        for vol in volumes:
            vol=vol['volumeId']
            if self.testmode and vol not in ('FFFBD'):
                continue
            vol_data=self.__get_volume_API__(vol)
            volume=Volume(
                name=vol_data['volumeId'],
                size=vol_data['cap_gb'],
                state=vol_data['status']
            )
            volume_info=volume.exportData()
            if volume_info:
                volume_list[volume_info['name']]=volume_info
        return volume_list
    
    def __get_volume_API__(self,volume):
        url=f'{self.connect_args2}/{self.storageId}/volume/{volume}'
        return self.__get_data_API__(url)
    
    def get_disks(self):
        return self.__get_disks_API__()

    def get_luns(self):
        return super().get_luns()

    def get_volumes(self):
        return self.__get_volumes_API__()

    def get_networks(self):
        return super().get_networks()

    def get_shelfs(self):
        return super().get_shelfs()

    def get_psu(self):
        return super().get_psu()

    def get_controllers(self):
        return super().get_controllers()