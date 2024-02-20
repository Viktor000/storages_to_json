class Network():
    def __init__(self,address,name='',netmask='',node='') -> None:
        self.address=address
        self.name=name
        self.netmask=netmask
        self.node=node
        
    def exportData(self):
        network_info={
            'address':self.address
        }
        if self.name:
            network_info['name']=self.name
        if self.netmask:
            network_info['netmask']=self.netmask
        if self.node:
            network_info['node']=self.node
        return network_info 