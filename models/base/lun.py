class Lun():
    def __init__(self,name,size,used='',path='',state='',node='',type='') -> None:
        self.name=name
        self.size=size
        self.used=used
        self.path=path
        self.state=state
        self.node=node
        self.type=type
        
    def exportData(self):
        lun_info={
            'name':self.name,
            'capacityGb':self.size
        }
        if self.used:
            lun_info['usedGb']=self.used 
        if self.path:
            lun_info['path']=self.path 
        if self.state:
            lun_info['state']=self.state 
        if self.node:
            lun_info['node']=self.node 
        if self.type:
            lun_info['type']=self.type    
        return lun_info