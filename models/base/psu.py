class Psu():
    def __init__(self,sn,partNum='',type='',shelf_id='') -> None:
        self.sn=sn
        self.partNum=partNum
        self.type=type     
        self.shelf_id=shelf_id
        
        
    def exportData(self):
        psu_info={
            'sn':self.sn
        }
        if self.partNum:
            psu_info['partNum']=self.partNum 
        if self.type:
            psu_info['type']=self.type
        if self.shelf_id:
            psu_info['shelf_id']=self.shelf_id
        return psu_info  