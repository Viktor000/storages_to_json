import pexpect
import sys
from pexpect import popen_spawn
from textfsm import clitable
import textfsm
import requests
import json
import logging
import time

from abc import ABC, abstractmethod
import platform
from pexpect import pxssh
from requests.auth import HTTPBasicAuth
from requests.packages import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)
logger = logging.getLogger(__name__)

result_file_path='/root/python_scripts/storage/result_data/'

class Storage(ABC):
    def __init__(self,address,vendor,model,access_type,json_file_name=''):
        self.vendor=vendor
        self.address=address
        self.model=model
        self.access_type=access_type
        self.file_path=json_file_name
        self.startTime=time.time()
        self.report={}
        logging.info(f"Storage {self.address} {self.vendor} {self.model} {self.access_type} is created")
        
    def collectData(self):
        logging.debug(f"Storage {self.address} {self.vendor} {self.model} {self.access_type} start collect data {time.time()-self.startTime}")
        self.disks=self.get_disks()
        self.luns=self.get_luns()
        self.volumes=self.get_volumes()
        self.networks=self.get_networks()
        self.shelfs=self.get_shelfs()
        self.psu=self.get_psu()
        self.controllers=self.get_controllers()
        
    def exportData(self):
        data = {
            self.address: {'name': self.address}
        }
        components = ['disks', 'luns', 'volumes', 'networks', 'shelfs', 'psu', 'controllers']
        for component in components:
            size=0
            value = getattr(self, component)
            if value:
                data[self.address][component] = value
                size=len(value)
            else:
                logging.info(f"{component.capitalize()} not found on {self.address}")
            self.report[component]=size
        return json.dumps(data)
    
    
    def exportDataToFile(self):
        #filename=f'{self.model}_{self.address}_{self.access_type}.json'
        file1 = open(f'{result_file_path}{self.file_path}.json', 'w')
        file1.write(self.exportData())
        file1.close()
        logging.debug(f"Storage {self.address} {self.vendor} {self.model} {self.access_type} exported in {round(time.time()-self.startTime,2)} seconds")

    @abstractmethod
    def get_disks(self):
        pass
    @abstractmethod
    def get_luns(self):
        pass
    
    @abstractmethod
    def get_volumes(self):
        pass
        
    @abstractmethod
    def get_networks(self):
        pass
    @abstractmethod
    def get_shelfs(self):
        pass
    
    @abstractmethod
    def get_psu(self):
        pass
    @abstractmethod
    def get_controllers(self):
        pass
    

    

    

    

    

















class CLI_Template_Storage(Storage):
    def __init__(self, address, vendor, model):
        super().__init__(address, vendor, model)
        self.access_type='CLI'
        if (platform.system() == "Windows"):
            self.util='naviseccli'
        else:
            self.util='/opt/Navisphere/bin/naviseccli'
        self.connect_args=f'-h {self.address}'
        self.connect_string=f'{self.util} {self.connect_args}'
        self.cli_table = clitable.CliTable('index', 'templates')
      
    def __get_data__(self,command):
        if (platform.system() == "Windows"):
            conn=pexpect.popen_spawn.PopenSpawn(f'{self.connect_string} {command}')
        else:
            conn=pexpect.spawn(f'{self.connect_string} {command}')
        conn.expect(pexpect.EOF)
        return conn.before.decode('utf8')
        
    def __get_disks__(self):
        command='getdisk'
        return self.__get_data__(command)
    
    def get_disks(self):
        attributes={'Command': 'getdisk', 'Vendor': self.vendor, 'Model':self.model}
        self.cli_table.ParseCmd(cmd_input=self.__get_disks__(),attributes=attributes)
        drives={}
        data_rows = [list(row) for row in self.cli_table]
        for row in data_rows:
            if row[8]:
                slot=f'{row[0]}-{row[1]}-{row[2]}'
                size=round(float(row[5])/1024/1024,2)
                drives[slot]={'slot':slot,
                              'vendor':row[3],
                              'status':row[4],
                              'rawSize':size,
                              'type':row[6],
                              'productId':row[7],
                              'partNum':row[9],
                              'sn':row[8]}
        return drives if drives else None
    
    def __get_luns_data__(self):
        command='lun -list -all'
        return self.__get_data__(command)
    
    def __get_luns_CLI__(self):
        attributes={'Command': 'lun -list -all', 'Vendor': self.vendor, 'Model':self.model}
        luns={}
        self.cli_table.ParseCmd(cmd_input=self.__get_luns_data__(),attributes=attributes)
        data_rows = [list(row) for row in self.cli_table]
        for row in data_rows:
            luns[row[0]]={'name':row[0],'capacityGb':row[1]}
        return luns
    
    def get_volumes(self):
        pass