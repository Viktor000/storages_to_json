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

class NetAppE(Storage):
    def __init__(self, address, vendor, model,access_type,username,password,json_file_path='./'):
        super().__init__(address, vendor, model,access_type,json_file_path)
        self.username=username
        self.password=password
        self.fwVersion=''
        if access_type=='CLI_file':
            filepath=address
            with open(filepath, "r") as f:
                self.allData=f.read()
        if access_type=='API':
            self.headers={}
            #self.basic = HTTPBasicAuth(self.username,self.password)
            #self.auth='https://{self.address}/ConfigurationManager/v1/objects/sessions'
            self.connect_args=f'https://{self.address}:8443/devmgr/v2/storage-systems'
            try:
                response = requests.get(self.connect_args,verify=False,headers=self.headers)
                data=response.json()
                self.storage_id=data[0]['id']
                self.connect_args=f'{self.connect_args}/{self.storage_id}'
            except Exception as e:
                print(e)    
       
    def __get_disks_CLI_file__(self):
        start_line='DRIVES------------------------------'
        end_line='DRIVE CHANNELS----------------------------'
        data= re.search(f'{start_line}(.*){end_line}', self.allData,re.DOTALL)[1]
        print (data)
        return self.allData   
       
       
    def __get_data_API__(self,url):
        try:
            response = requests.get(url,verify=False,headers=self.headers)
            return(response.json())
        except Exception as e:
            print(e)    
            
    def __get_disks_API__(self):
        url=f'{self.connect_args}/drives'
        data=self.__get_data_API__(url)
        hdd_list={}
        for disk in data:
            drive=Drive(
                slot=disk['physicalLocation']['slot'],
                model=disk['productID'],
                size=round(float(disk['rawCapacity']/1000/1000/1000/1000),2),
                type=disk['phyDriveType'],
                sn=disk['serialNumber'],
                vendor=disk['manufacturer'],
                status=disk['status']
                )
            disks_info=drive.exportData()
            if disks_info:
                hdd_list[disks_info['slot']]=disks_info
        return hdd_list        
       
    def __get_volumes_API__(self):
        url=f'{self.connect_args}/volumes'
        data=self.__get_data_API__(url)   
        for volume in data:
            vol=Volume(
                name=volume['name'],
                size=round(float(volume['capacity']/1000/1000/1000),2),
                status=volume['status']
                )
            volumes_info=vol.exportData()
            if volumes_info:
                self.volumes[volumes_info['name']]=volumes_info
            
        
    def __get_controllers_API__(self):
        url=f'{self.connect_args}/controllers'
        data=self.__get_data_API__(url)   
        for controller in data:
            contr=Controller(
                id=controller['id'],
                sn=controller['serialNumber'],
                partNum=controller['partNumber'],
                model=controller['modelName']
                )
            controllers_info=contr.exportData()
            if controllers_info:
                self.controllers[controllers_info['id']]=controllers_info
           
           
    def __get_psu_API__(self):
        url=f'{self.connect_args}/hardware-inventory'
        data=self.__get_data_API__(url)['powerSupplies']
        for psu in data:
            psu=Psu(
                sn=psu['serialNumber'],
                partNum=psu['partNumber'],
                type=psu['fruType']
                )
            psus_info=psu.exportData()
            if psus_info:
                self.psu[psus_info['sn']]=psus_info       
                
                
    def __get_networks_API__(self):
        url=f'{self.connect_args}/hardware-inventory'
        data=self.__get_data_API__(url)['controllers']
        for controller in data:
            nets=controller['netInterfaces']
            for network in nets:
                net=Network(
                    address=network['ipv4Address'],
                    name=network['interfaceName'],
                    netmask=network['ipv4SubnetMask'],
                    node=controller['id']
                    )
                networks_info=net.exportData()
                if networks_info:
                    self.networks[f'{controller['id']}+{networks_info['name']}']=networks_info
                
                
    def get_disks(self):
        if self.access_type=='CLI_file':
            return self.__get_disks_CLI_file__() 
        if self.access_type=='API':
            return self.__get_disks_API__()      
    def get_controllers(self):
        return self.__get_controllers_API__()
    
    def get_shelfs(self):
        return super().get_shelfs()
    
    def get_luns(self):
        return super().get_luns()
    
    def get_networks(self):
        return self.__get_networks_API__()
    
    def get_psu(self):
        return self.__get_psu_API__()
    
    def get_volumes(self):
        return self.__get_volumes_API__()