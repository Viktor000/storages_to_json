
import platform
from requests.auth import HTTPBasicAuth
import requests
import pexpect
from textfsm import clitable
import logging

from models.base.storage import Storage
from models.base.drive import Drive
from models.base.lun import Lun
from models.base.volume import Volume
from models.base.network import Network
from models.base.shelf import Shelf
from models.base.psu import Psu
from models.base.controller import Controller

from requests.packages import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)
import re 


logger = logging.getLogger(__name__)
class NetApp(Storage):
    def __init__(self, address, vendor, model,access_type,username,password,json_file_path='./'):
        super().__init__(address, vendor, model,access_type,json_file_path)
        self.username=username
        self.password=password
        self.ssh=''
        self.fwVersion=''
        if access_type=='API':
            self.headers={}
            self.basic = HTTPBasicAuth(self.username,self.password)
            self.connect_args=f'https://{self.address}/api'
        elif access_type=='CLI':
            if self.username.find('\\'):
                self.username=self.username.replace('\\','\\\\')               
            if (platform.system() == "Windows"):
                self.ssh= pexpect.popen_spawn.PopenSpawn(f'ssh {self.address} -l {self.username}')
            else:
                self.ssh= pexpect.spawn(f'ssh {self.address} -l {self.username}')
            #self.ssh.logfile = sys.stdout.buffer
            pattern_index = self.ssh.expect(["The authenticity of host", "[Pp]assword:"])
            if pattern_index == 0:
                self.ssh.sendline('yes')
                self.ssh.expect('[Pp]assword:')
                self.ssh.sendline(self.password)
            else:
                self.ssh.sendline(self.password)
            
            self.ssh.expect('>')
            self.ssh.sendline('set -rows 0;set -units GB')
            self.ssh.expect('>')
            self.ssh.sendline('version')
            self.ssh.expect('>')
            try:
                self.fwVersion=float(re.search('NetApp Release (\d+\.\d+).*:.*',self.ssh.before.decode('utf-8'))[1])
            except Exception as e:
                logger.info(e)
            
            self.cli_table = clitable.CliTable('index', 'templates')

    def __del__(self):
        #print(self.exportData())
        if self.access_type=='CLI':
            self.ssh.close()
        
    def __get_data_CLI__(self,command):
        logger.debug(f'NetApp {self.address} {self.access_type} send command: {command}')
        self.ssh.sendline(command)
        self.ssh.expect('>')
        return self.ssh.before.decode('utf8')
        
    def __get_data_API__(self,url):
        try:
            response = requests.get(url,verify=False,headers=self.headers,auth=self.basic)
            #print(url)
            #print(response)
            return(response.json())
        except Exception as e:
            print(e)      
    
    def __get_disks_CLI__(self):  
        #command='storage disk show -fields disk,type,model,serialnumber,vendor,home,capacity-sectors,bps,physicalsize,usedsize'
        attributes={'Command': 'storage disk show -fields disk,type,model,serialnumber,vendor,home,capacity-sectors,bps,physicalsize,usedsize,position',
                    'Vendor': self.vendor, 'Model':self.model}
        self.cli_table.ParseCmd(cmd_input=self.__get_data_CLI__(attributes['Command']),attributes=attributes)
        drives={}
        data_rows = [list(row) for row in self.cli_table]
        for row in data_rows:
            drive=Drive(
                slot=row[0],
                vendor=row[10],
                model=row[4],
                size=round(int(row[2])*int(row[1])/1000/1000/1000/1000,2),
                type=row[8],
                sn=row[7],
                status=row[6],
                node=row[3]
            )
            drives[row[0]]=drive.exportData()
        return drives if drives else None
    
     
    def __get_disks_API__(self):
        url=f'{self.connect_args}/storage/disks/'
        data=self.__get_data_API__(url)['records']
        hdd_list={}
        for disk in data:
            disks_info=self.__get_disk_API__(disk['name'])
            if disks_info:
                hdd_list[disks_info['slot']]=disks_info
        return hdd_list
    
    def __get_disk_API__(self,disk_id):
        url=f'{self.connect_args}/storage/disks/{disk_id}'
        data=self.__get_data_API__(url)
        if 'node' in data:
            disk_node=data['node']['name']
        else:
            disk_node=None

        drive=Drive(
            slot=data['name'],
            vendor=data['vendor'],
            model=data['model'],
            size=round(data['physical_size']/1000/1000/1000/1000,2),
            type=data['type'],
            sn=data['serial_number'],
            status=data['state'],
            node=disk_node
        )
        disk_info=drive.exportData()
        #print(disk_info)
        return disk_info if disk_info else None
    
    def __get_luns_API__(self):
        url=f'{self.connect_args}/storage/luns/'
        data=self.__get_data_API__(url)['records']
        luns_list={}
        for lun in data:
            luns_info=self.__get_lun_API__(lun['uuid'])
            if luns_info:
                luns_list[luns_info['name']]=luns_info
        return luns_list
    
    def __get_luns_CLI__(self):
        attributes={'Command': 'lun show -fields Vserver,volume,path,State,ostype,Size,node,size-used',
                    'Vendor': self.vendor, 'Model':self.model}
        self.cli_table.ParseCmd(cmd_input=self.__get_data_CLI__(attributes['Command']),attributes=attributes)
        #self.cli_table.ParseCmd(ddd,attributes=attributes)
        data_rows = [list(row) for row in self.cli_table]
        luns_list={}
        for row in data_rows:
            lun=Lun(
                name=row[1],
                size=row[3],
                used=row[6],
                state=row[5],
                node=row[7],
                type=row[4]
            )
            luns_list[row[1]]=lun.exportData()
        return luns_list if luns_list else None
    
    def __get_lun_API__(self,lun_uuid):
        url=f'{self.connect_args}/storage/luns/{lun_uuid}'
        data=self.__get_data_API__(url)
        # lun_info={
        #    'name':data['name'],
        #    'capacityGb':round(data['space']['size']/1000/1000/1000,2),
        #    'usedGb':round(data['space']['used']/1000/1000/1000,2)
        # }
        lun=Lun(
            name=data['name'],
            size=round(data['space']['size']/1000/1000/1000,2),
            used=round(data['space']['used']/1000/1000/1000,2)
        )
        lun_info=lun.exportData()
        return lun_info if lun_info else None
        
    def __get_volumes_CLI__(self):
        attributes={'Command': 'volume show -fields vserver,volume,aggregate,size,state,used,junction-path,files,security-style',
                    'Vendor': self.vendor, 'Model':self.model}
        self.cli_table.ParseCmd(cmd_input=self.__get_data_CLI__(attributes['Command']),attributes=attributes)
        #print(self.cli_table)
        data_rows = [list(row) for row in self.cli_table]
        volumes_list={}
        for row in data_rows:
            #print (row)
            volume=Volume(
                name=row[1],
                size=row[3],
                used=row[6],
                server=row[0],
                aggregate=row[2],
                state=row[4],
                path=row[5],
                securityStyle=row[7],
                files=row[8]
            )
            volumes_list[f'{row[0]}+{row[1]}']=volume.exportData()
    
        return volumes_list if volumes_list else None
        
        
    def __get_volumes_API__(self):
        url=f'{self.connect_args}/storage/volumes/'
        data=self.__get_data_API__(url)['records']
        volumes_list={}
        for volume in data:
            volumes_info=self.__get_volume_API__(volume['uuid'])
            if volumes_info:
                volumes_list[volumes_info['name']]=volumes_info
        return volumes_list
    
    def __get_volume_API__(self,volume_uuid):
        url=f'{self.connect_args}/storage/volumes/{volume_uuid}'
        data=self.__get_data_API__(url)
        volume=Volume(
            name=data['name'],
            size=round(data['space']['size']/1000/1000/1000,2),
            used=round(data['space']['used']/1000/1000/1000,2)
        )
        volume_info=volume.exportData()
        return volume_info if volume_info else None
    
    def __get_networks_CLI__(self):
        attributes={'Command': 'network interface show -fields vserver,address,netmask,home-node,data-protocol -data-protocol nfs',
                    'Vendor': self.vendor, 'Model':self.model}
        self.cli_table.ParseCmd(cmd_input=self.__get_data_CLI__(attributes['Command']),attributes=attributes)
        #print(self.cli_table)
        data_rows = [list(row) for row in self.cli_table]
        #print(data_rows)
        networks_list={}
        for row in data_rows:
            network=Network(
                address=row[3],
                name=f'{row[0]}+{row[1]}',
                netmask=row[4],
                node=row[5]
            )
            # print(row)
            # print(network.exportData())
            networks_list[f'{row[0]}+{row[1]}']=network.exportData()
        return networks_list if networks_list else None
    
    def __get_shelfs_CLI__(self):
        attributes={'Command': 'storage shelf show -fields serial-number,product-id,shelf-id',
                    'Vendor': self.vendor, 'Model':self.model}
        self.cli_table.ParseCmd(cmd_input=self.__get_data_CLI__(attributes['Command']),attributes=attributes)
        #print(self.cli_table)
        data_rows = [list(row) for row in self.cli_table]
        #print(data_rows)
        shelfs_list={}
        for row in data_rows:
            shelf=Shelf(
                shelf_id=row[0],
                model=row[1],
                sn=row[2]
            )
            shelfs_list[row[0]]=shelf.exportData()
        return shelfs_list if shelfs_list else None   
    
    def __get_psu_CLI__(self):
        attributes={'Command': 'storage shelf show -fields psu-serial-number,psu-part-number,psu-type,shelf-id',
                    'Vendor': self.vendor, 'Model':self.model}
        
        
        self.cli_table.ParseCmd(cmd_input=self.__get_data_CLI__(attributes['Command']),attributes=attributes)
        data_rows = [list(row) for row in self.cli_table]
        psu_list={}
        for row in data_rows:
            elems=row[1].count(',')+1
            psu_list[row[0]]={}
            for elem in range(0,elems):
                psu=Psu(
                    sn=row[3].split(',')[elem],
                    partNum=row[2].split(',')[elem],
                    type=row[1].split(',')[elem],
                    shelf_id=row[0],
                )
                psu_list[row[0]][row[3].split(',')[elem]]=psu.exportData()
        return psu_list if psu_list else None 
        
    def __get_controllers_CLI__(self):

        attributes={'Command': 'system controller memory dimm show -fields serial,part-no,node',
                    'Vendor': self.vendor, 'Model':self.model}
        self.cli_table.ParseCmd(cmd_input=self.__get_data_CLI__(attributes['Command']),attributes=attributes)
        #print(self.cli_table)
        ram_rows = [list(row) for row in self.cli_table]
        ram_list={}
        for row in ram_rows:
            if not ram_list.get(row[0]):
                ram_list[row[0]]={}
            ram_list[row[0]][row[1]]={
                'sn':row[2],
                'parnNum':row[3]
                }
        #print(ram_list)
        attributes={'Command': 'system controller bootmedia show -fields node,serial-num,unique-name',
                    'Vendor': self.vendor, 'Model':self.model}
        self.cli_table.ParseCmd(cmd_input=self.__get_data_CLI__(attributes['Command']),attributes=attributes)
        #print(self.cli_table)
        boot_rows = [list(row) for row in self.cli_table]
        boot_list={}
        for row in boot_rows:
            boot_list[row[0]]={
                'sn':row[1],
                'name':row[2].strip()
                }



        attributes={'Command': 'system controller show -fields serial-number,part-number,model,system-id',
                    'Vendor': self.vendor, 'Model':self.model}
        self.cli_table.ParseCmd(cmd_input=self.__get_data_CLI__(attributes['Command']),attributes=attributes)
        #print(self.cli_table)
        controller_rows = [list(row) for row in self.cli_table]
        controllers_list={}
        for row in controller_rows:
            controller=Controller(
                id=row[1],
                node=row[0],
                sn=row[2],
                partNum=row[3],
                model=row[4],
                ram=ram_list.get(row[0]),
                bootmedia=boot_list.get(row[0])
            )
            controllers_list[row[0]]=controller.exportData()
        return controllers_list if controllers_list else None 
            
    def __get_networks_API__(self):
        pass
    
    def get_disks(self):
        if self.access_type=='API':
            return self.__get_disks_API__()
        elif self.access_type=='CLI':
            return self.__get_disks_CLI__()
    
    def get_luns(self):
        if self.access_type=='API':
            return self.__get_luns_API__()
        elif self.access_type=='CLI':
            return self.__get_luns_CLI__()
    
    def get_volumes(self):
        if self.access_type=='API':
            return self.__get_volumes_API__()
        elif self.access_type=='CLI':
            return self.__get_volumes_CLI__()
        
    def get_networks(self):
        if self.access_type=='API':
            return self.__get_networks_API__()
        elif self.access_type=='CLI':
            return self.__get_networks_CLI__()
    def get_shelfs(self):
        if self.access_type=='API':
            pass
            #return self.__get_shelfs_API__()
        elif self.access_type=='CLI':
            return self.__get_shelfs_CLI__()
        
    def get_psu(self):
        if self.access_type=='CLI':
            return self.__get_psu_CLI__()
    def get_controllers(self):
        if self.access_type=='CLI':
            return self.__get_controllers_CLI__()
