class Shelf():
    def __init__(self,shelf_id,model='',sn='',partNum='') -> None:
        self.shelf_id=shelf_id
        self.model=model
        self.sn=sn    
        self.partNum=partNum 
        
    def exportData(self):
        shelf_info={
            'shelf_id':self.shelf_id
        }
        if self.model:
            shelf_info['model']=self.model
        if self.sn:
            shelf_info['sn']=self.sn 
        if self.partNum:
            shelf_info['partNum']=self.partNum 
        return shelf_info  