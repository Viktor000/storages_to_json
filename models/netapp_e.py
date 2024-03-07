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

class NetAppE(Storage):
    def __init__(self, address, vendor, model,access_type,username,password,json_file_path='./'):
        super().__init__(address, vendor, model,access_type,json_file_path)
        self.username=username
        self.password=password
        self.ssh=''
        self.fwVersion=''
        if access_type=='CLI_file':
            filepath=address
            with open(filepath, "r") as f:
                self.allData=f.read()
            
       
    def __get_disks_CLI_file__(self):
        start_line='DRIVES------------------------------'
        end_line='DRIVE CHANNELS----------------------------'
        data= re.search(f'{start_line}(.*){end_line}', self.allData,re.DOTALL)[1]
        print (data)
        return self.allData   
       
       
       
       
    def get_disks(self):
        if self.access_type=='CLI_file':
            return self.__get_disks_CLI_file__()     
        
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