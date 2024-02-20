class Volume():
    def __init__(self,name,size,used='',server='',aggregate='',state='',path='',securityStyle='',files='') -> None:
        self.name=name
        self.size=size
        self.used=used
        self.server=server
        self.aggregate=aggregate
        self.state=state
        self.path=path
        self.securityStyle=securityStyle
        self.files=files
        
    def exportData(self):
        volume_info={
            'name':self.name,
            'capacityGb':self.size, 
        }
        if self.used:
            volume_info['usedGb']=self.used 
        if self.server:
            volume_info['server']=self.server
        if self.aggregate:
            volume_info['aggregate']=self.aggregate
        if self.state:
            volume_info['state']=self.state
        if self.path:
            volume_info['path']=self.path
        if self.securityStyle:
            volume_info['securityStyle']=self.securityStyle
        if self.files:
            volume_info['files']=self.files
        return volume_info  