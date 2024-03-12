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
            self.connect_args=f'http://{self.address}:8443/devmgr/v2/storage-systems'
            try:
                response = requests.get(self.connect_args,verify=False,headers=self.headers)
                data=response.json()
                #print ('++++++++++++++++++++++')
                #print(data)
                self.storage_id=data[0]['id']
                self.connect_args=f'{self.connect_args}/{self.storage_id}'
            except Exception as e:
                print ('------------------------------------')
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
        url=f'{self.connect_args}/hardware-inventory'
        data=self.__get_data_API__(url)
        data_drives=data['drives']
        data_drawers=data['drawers']
        data_shelfs=data['trays']
        shelfs_info={}
        drawers_info={}
        
        
        for shelf in data_shelfs:
            shelfs_info[shelf['trayRef']]=shelf['trayId']
        for drawer in data_drawers:
            drawers_info[drawer['drawerRef']]={'tray':drawer['physicalLocation']['trayRef'],
                                               'name':drawer['physicalLocation']['label']}
        
        hdd_list={}
        for disk in data_drives:
            # print(shelfs_info[disk["physicalLocation"]["trayRef"]])
            # print(drawers_info[disk["physicalLocation"]["locationParent"]["typedReference"]["symbolRef"]]["name"])
            # print(disk["physicalLocation"]["label"])
            
            slot=f'{shelfs_info[disk["physicalLocation"]["trayRef"]]}.'\
                 f'{drawers_info[disk["physicalLocation"]["locationParent"]["typedReference"]["symbolRef"]]["name"]}.'\
                 f'{disk["physicalLocation"]["label"]}'
            #print(slot)
            drive=Drive(
                slot=slot,
                model=disk['productID'],
                size=round(float(disk['rawCapacity'])/1000/1000/1000/1000,2),
                type=disk['phyDriveType'].upper(),
                sn=disk['serialNumber'].strip(),
                vendor=disk['manufacturer'].strip(),
                status=disk['status']
                )
            disks_info=drive.exportData()
            if disks_info:
                hdd_list[disks_info['slot']]=disks_info
        return hdd_list        
       
    def __get_volumes_API__(self):
        url=f'{self.connect_args}/volumes'
        data=self.__get_data_API__(url)  
        #print (data) 
        list_volumes={}
        for volume in data:
            #print(volume)
            vol=Volume(
                name=volume['name'],
                size=round(float(volume['capacity'])/1000/1000/1000,2),
                state=volume['status'].strip()
                )
            volumes_info=vol.exportData()
            if volumes_info:
                list_volumes[volumes_info['name']]=volumes_info
        return list_volumes
            
        
    def __get_controllers_API__(self):
        url=f'{self.connect_args}/controllers'
        data=self.__get_data_API__(url)  
        list_controllers={} 
        for controller in data:
            contr=Controller(
                id=controller['id'].strip(),
                sn=controller['serialNumber'].strip(),
                partNum=controller['partNumber'].strip(),
                model=controller['modelName'].strip(),
                node=controller['physicalLocation']['label'].strip()
                )
            controllers_info=contr.exportData()
            if controllers_info:
                list_controllers[controllers_info['id']]=controllers_info
        return list_controllers
           
           
    def __get_psu_API__(self):
        url=f'{self.connect_args}/hardware-inventory'
        data=self.__get_data_API__(url)
        data_psu=data['powerSupplies']
        data_shelfs=data['trays']
        shelfs_info={}

        for shelf in data_shelfs:
            shelfs_info[shelf['trayRef']]=str(shelf['trayId'])+'.'
        
        list_psu={}
        for psu in data_psu:
            shelf_id=shelfs_info[psu['physicalLocation']['trayRef']]
            psu=Psu(
                sn=psu['serialNumber'].strip(),
                partNum=psu['partNumber'].strip(),
                type=psu['fruType'].strip()
                )
            psus_info=psu.exportData()
            if psus_info:
                if shelf_id not in list_psu:
                    list_psu[shelf_id]={}
                list_psu[shelf_id][psus_info['sn']]=psus_info   
        return list_psu    
                
    def __get_shelfs_API__(self):
        url=f'{self.connect_args}/hardware-inventory'
        data=self.__get_data_API__(url)['trays']
        list_shelfs={}
        for shelf in data:
            shelf=Shelf(
                shelf_id=str(shelf['trayId'])+'.',
                model=shelf['partNumber'].strip(),
                sn=shelf['serialNumber'].strip()
                )
            shelfs_info=shelf.exportData()
            if shelfs_info:
                list_shelfs[shelfs_info['shelf_id']]=shelfs_info
        return list_shelfs
                
    def __get_networks_API__(self):
        url=f'{self.connect_args}/hardware-inventory'
        data=self.__get_data_API__(url)['controllers']
        list_networks={}
        for controller in data:
            nets=controller['netInterfaces']
            for network in nets:
                network=network['ethernet']
                #print (network)
                net=Network(
                    address=network['ipv4Address'].strip(),
                    name=network['interfaceName'].strip(),
                    netmask=network['ipv4SubnetMask'].strip(),
                    node=controller['id'].strip()
                    )
                networks_info=net.exportData()
                if networks_info:
                    list_networks[f'{controller["id"]}+{networks_info["name"]}']=networks_info
        return list_networks
                
                
    def get_disks(self):
        if self.access_type=='CLI_file':
            return self.__get_disks_CLI_file__() 
        if self.access_type=='API':
            return self.__get_disks_API__()      
    def get_controllers(self):
        return self.__get_controllers_API__()
    
    def get_shelfs(self):
        return self.__get_shelfs_API__()
    
    def get_luns(self):
        return super().get_luns()
    
    def get_networks(self):
        return self.__get_networks_API__()
    
    def get_psu(self):
        return self.__get_psu_API__()
    
    def get_volumes(self):
        return self.__get_volumes_API__()