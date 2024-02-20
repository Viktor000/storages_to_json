class Drive():       
    def __init__(self,slot,vendor,model,size,type,sn,partNum='',status='',node=''):
        self.slot=slot
        self.vendor=vendor
        self.model=model
        self.size=size
        self.type=type
        self.sn=sn
        self.partNum=partNum
        self.status=status
        self.node=node
        
    def exportData(self):
        disk_info={
            'slot':self.slot,
            'vendor':self.vendor,
            'rawSize':self.size,
            'type':self.type,
            'productId':self.model,
            'sn':self.sn}
        if self.partNum:
            disk_info['partNum']=self.partNum 
        if self.status:
            disk_info['status']=self.status
        if self.node:
            disk_info['node']=self.node                    
        return disk_info