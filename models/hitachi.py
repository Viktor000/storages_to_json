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

class Hitachi(Storage):
    def __init__(self, address, vendor, model,access_type,username,password,json_file_path='./'):
        super().__init__(address, vendor, model,access_type,json_file_path)
        self.username=username
        self.password=password
        self.fwVersion=''
        if access_type=='API':
            self.headers={}
            self.basic = HTTPBasicAuth(self.username,self.password)
            self.auth='https://{self.address}/ConfigurationManager/v1/objects/sessions'
            self.connect_args=f'https://{self.address}/ConfigurationManager/v1/objects/'
            try:
                response = requests.post(self.auth,verify=False,headers=self.headers,auth=self.basic)
                self.token=response.json()['token']
                self.headers={'Authorization':f'Session {self.token}'}
            except Exception as e:
                print(e)    
                
            try:
                response = requests.get(self.connect_args+'storages',verify=False,headers=self.headers)
                data=response.json()['data']
                for dev in data:
                    if dev['svpIp']==self.address:
                        self.storageId=dev['storageDeviceId']
                        self.connect_args=f'{self.connect_args}storages/{self.storageId}/'
                        break
            except Exception as e:
                print(e)    
            
    def __get_data_API__(self,url):
        try:
            response = requests.get(url,verify=False,headers=self.headers)
            return(response.json())
        except Exception as e:
            print(e)     
            
    def __get_disks_API__(self):
        url=f'{self.connect_args}drives'
        data=self.__get_data_API__(url)['data']
        hdd_list={}
        for disk in data:
            drive=Drive(
                    slot=disk['driveLocationId'],
                    model=disk['driveType'],
                    size=round(float(disk['totalCapacity']/1000),2),
                    type=disk['driveTypeName'],
                    status=disk['status'],
                    node=disk['parityGroupId']
                    )
            disks_info=drive.exportData()
            if disks_info:
                hdd_list[disks_info['slot']]=disks_info
        return hdd_list
    
            
    def get_disks(self):
        return self.__get_disks_API__()   
        
    def get_controllers(self):
        return super().get_controllers()
    
    def get_shelfs(self):
        return super().get_shelfs()
    
    def get_luns(self):
        return super().get_luns()
    
    def get_networks(self):
        return super().get_networks()
    
    def get_psu(self):
        return super().get_psu()
    
    def get_volumes(self):
        return super().get_volumes()