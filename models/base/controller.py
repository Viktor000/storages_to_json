class Controller():
    def __init__(self,id,node='',sn='',partNum='',model='',cpu='',ram='',bootmedia='') -> None:
        self.id=id
        self.node=node
        self.sn=sn   
        self.partNum=partNum 
        self.model=model
        self.cpu=cpu
        self.ram=ram
        self.bootmedia=bootmedia 
        
        
    def exportData(self):
        controller_info={
            'id':self.id
        }
        if self.node:
            controller_info['node']=self.node 
        if self.sn:
            controller_info['sn']=self.sn 
        if self.partNum:
            controller_info['partNum']=self.partNum 
        if self.model:
            controller_info['model']=self.model
        if self.cpu:
            controller_info['cpu']=self.cpu
        if self.ram:
            controller_info['ram']=self.ram
        if self.bootmedia:
            controller_info['bootmedia']=self.bootmedia
  
        return controller_info  