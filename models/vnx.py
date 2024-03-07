import platform
import logging

from models.base.storage import Storage

from models.base.drive import Drive
from models.base.lun import Lun
from models.base.volume import Volume
from models.base.network import Network
from models.base.shelf import Shelf
from models.base.psu import Psu
from models.base.controller import Controller


import pexpect
from textfsm import clitable
logger = logging.getLogger(__name__)
class VNX(Storage):
    def __init__(self, address, vendor, model,access_type,username,password,json_file_path='./'):
        super().__init__(address, vendor, model,access_type,json_file_path)
        self.username=username
        self.password=password
        if access_type=='CLI':
            if (platform.system() == "Windows"):
                self.util='naviseccli'
            else:
                self.util='/opt/Navisphere/bin/naviseccli'
            self.connect_args=f'-h {self.address} -User {self.username} -Password {self.password} -Scope 0'
            self.connect_string=f'{self.util} {self.connect_args}'
            self.cli_table = clitable.CliTable('index', 'templates')
        elif access_type=='API':
            print (F'This Device {self.address} {self.vendor} {self.model} did not support access type {access_type}')
            exit()
      
    def __get_data_CLI__(self,command):
        logger.debug(f'EMC VNX {self.address} {self.access_type} send command: {command}')
        if (platform.system() == "Windows"):
            conn=pexpect.popen_spawn.PopenSpawn(f'{self.connect_string} {command}')
        else:
            conn=pexpect.spawn(f'{self.connect_string} {command}')
        conn.expect(pexpect.EOF)
        return conn.before.decode('utf8')
        
    
    def __get_disks_CLI__(self):
        attributes={'Command': 'getdisk', 'Vendor': self.vendor, 'Model':self.model}
        self.cli_table.ParseCmd(cmd_input=self.__get_data_CLI__(attributes['Command']),attributes=attributes)
        drives={}
        data_rows = [list(row) for row in self.cli_table]
        for row in data_rows:
            if row[8]:
                slot=f'{row[0]}-{row[1]}-{row[2]}'
                size=round(float(row[5])/1024/1024,2)
                drive=Drive(
                    slot=slot,
                    vendor=row[3],
                    model=row[7],
                    size=size,
                    type=row[6],
                    sn=row[8],
                    partNum=row[9],
                    status=row[4]
                )
                drives[slot]=drive.exportData()
        return drives if drives else None
    
    def __get_luns_CLI__(self):
        attributes={'Command': 'lun -list -all', 'Vendor': self.vendor, 'Model':self.model}
        luns={}
        self.cli_table.ParseCmd(cmd_input=self.__get_data_CLI__(attributes['Command']),attributes=attributes)
        data_rows = [list(row) for row in self.cli_table]
        for row in data_rows:
            lun=Lun(
                name=row[0],
                size=row[1]
            )
            luns[row[0]]=lun.exportData()
        return luns
    
    def __get_psu_CLI__(self):
        attributes={'Command': 'getresume -ps', 'Vendor': self.vendor, 'Model':self.model}
        psu_list={}
        self.cli_table.ParseCmd(cmd_input=self.__get_data_CLI__(attributes['Command']),attributes=attributes)
        data_rows = [list(row) for row in self.cli_table]
        count=0
        for row in data_rows:
            psu=Psu(
                sn=row[3],
                partNum=row[2],
                type=row[1]
            )
            if str(count) not in psu_list:
                psu_list[str(count)]={}
            psu_list[str(count)][row[3]]=psu.exportData()
            count+=1
        return psu_list
    
    
    def __get_shelfs_CLI__(self):
        attributes={'Command': 'getresume -mp', 'Vendor': self.vendor, 'Model':self.model}
        shelf_list={}
        self.cli_table.ParseCmd(cmd_input=self.__get_data_CLI__(attributes['Command']),attributes=attributes)
        data_rows = [list(row) for row in self.cli_table]
        count=0
        for row in data_rows:
            shelf=Shelf(
                #shelf_id=row[0],
                shelf_id=str(count),
                model=row[1],
                sn=row[3],
                partNum=row[2]
            )
            shelf_list[str(count)]=shelf.exportData()
            count+=1
        return shelf_list
    
    def __get_controllers_CLI__(self):
        attributes={'Command': 'getresume -sp', 'Vendor': self.vendor, 'Model':self.model}
        controllers_list={}
        self.cli_table.ParseCmd(cmd_input=self.__get_data_CLI__(attributes['Command']),attributes=attributes)
        data_rows = [list(row) for row in self.cli_table]
        for row in data_rows:
            controller=Controller(
                id=row[0],
                model=row[1],
                sn=row[3],
                partNum=row[2],
                node=row[0]
            )
            controllers_list[row[0]]=controller.exportData()
        return controllers_list
    
    def __get_volumes_CLI__(self):
        pass

    def __get_networks_CLI__(self):
        pass

    def get_disks(self):
        if self.access_type=='CLI':
            return self.__get_disks_CLI__()
    
    def get_luns(self):
        if self.access_type=='CLI':
            return self.__get_luns_CLI__()
    
    def get_volumes(self):
        if self.access_type=='CLI':
            return self.__get_volumes_CLI__()
        
    def get_networks(self):
        if self.access_type=='CLI':
            return self.__get_networks_CLI__()
    
    def get_shelfs(self):
        if self.access_type=='CLI':
            return self.__get_shelfs_CLI__()
        

    def get_psu(self):
        if self.access_type=='CLI':
            return self.__get_psu_CLI__()
        
    def get_controllers(self):
        if self.access_type=='CLI':
            return self.__get_controllers_CLI__()
    