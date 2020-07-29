'''
Created on 31 июл. 2020 г.

@author: ladmin
'''
import os, stat, re
from fabric import  colors, api as fab
from abc import ABC, abstractmethod, abstractproperty
from srv.objectlib import Networker

class ExecStrategy(ABC):
    
    def __init__(self, element):
        self._element=element
    def updateRole(self):
        print('Update Role')
        str=' '
        fab.env.host_string=str.join(fab.env.roledefs[str.join(self._element._role)])
      
    @abstractmethod
    def fullcycle(self):
        self.prepare()
    
    @abstractmethod
    def prepare(self):
        self._element.runrepo()  
    @abstractmethod
    def initRepo(self):
        pass
    
    def accompaniment(self):
        self.makeNetwork()
        self.makeVolume()   
    
    def migrate(self, tag=None):
        self._element.initservice()
        self.accompaniment()
        self._element.updateFromImage(force=True, tag=tag)
         
    def makeVolume(self):
        if hasattr(self._element, '_Element__vols'):
            vols=self._element.volumes
            for vol in vols:
                vols[vol].update()
    
    def makeNetwork(self):
        if hasattr(self._element, '_Element__net'):
            self._element.network.update()

class ConstructStrategy(ExecStrategy):
    def initRepo(self, branch='master'):
        repo=self._element.initRepoForLayer(branch)
        return repo
    
    def prepare(self):
        self.accompaniment()
        self._element.hook()
        self._element.initservice()
 
        
    def fullcycle(self):
        self.prepare()
        self._element.deploy()
        fab.env.host=None
        fab.env.host_string=None
        
class CommonStrategy(ExecStrategy):
    def initRepo(self, branch='master'):
        repo=self._element.initRepoForLayer(branch)
        return repo
    def prepare(self):
        self.accompaniment()
        self._element.hook()
        self._element._dockerfileObj.buildfile()
        self._element.initservice()
    
    def fullcycle(self, force=True):
        self.prepare()
        
        #self._element.push()
        #self._element.backup()
        #self._element.pull()
        #self._element.migrate()
        #self._element.update()
        #self._element.upgrade()
        
        self._element.deploy()
        fab.env.host=None
        fab.env.host_string=None
        
        
class CommonStrategyForNginx(ExecStrategy):
    
    def initRepo(self, branch='master'):
        repo=self._element.initRepoForLayer(branch)
        return repo
    
    def prepare(self):
        self.accompaniment()
        self._element.hook()
        self._element._dockerfileObj.buildfile()
        self._element.initservice() 
    
    def fullcycle(self):
        #tag=None
        #force=False
        #backup=False
        #migrate=True
        
        self.prepare()
        #self._element.deploy2(tag='127.0.0.1:5000/itcluster/nginx:latest')
        self._element.deploy()
        #self._element.prepare()
        #self._element.push()
        #fab.execute(
        #    self._element.upgrade,
        #    tag=tag,
        #    force=force,
        #    backup=backup,
        #    migrate=migrate,
        #)
        fab.env.host=None
        fab.env.host_string=None
        
    def putStream(self, streamname, content):
        fullname=os.path.join(os.getcwd(), streamname+'.conf')
        try:
            os.remove(fullname)
            file = open(fullname, 'w')
            # Do something with the file
        except IOError:
            file = open(fullname, 'w')
        file.write(content)   
        file.close()
        self._element._dockerfileObj.ADD(streamname+'.conf', '/etc/nginx/conf.d/'+streamname+'.conf', index=35)
        
        
        
class CommonStrategyForPhp(ExecStrategy):
    
    def prepare(self):
        self.accompaniment()
        self._element.hook()
        self._element._dockerfileObj.buildfile()
        self._element.initservice() 
    
    def fullcycle(self):    
        self.prepare()
        self._element.deploy()
        fab.env.host=None
        fab.env.host_string=None
        
    def initRepo(self, branch='master'):
        repo=self._element.initRepoForLayer(branch)
        return repo

    def getStreamConfig(self):
        self.updateRole()
        f=fab.env
        str=' '

        netId=self._element._service.info['Spec']['TaskTemplate']['Networks']
        net=self._element._service.network
        print(net)
        netName=str.join(net)
        networker=Networker(netName)
        iplist=networker.getRelateIpList(filter=self._element.myname)
        template='upstream '+self._element.myname+' {\n'
        for curName in iplist.keys():
            template=template+'server '+iplist[curName]+':9000 weight=2 max_fails=2 fail_timeout=2s;\n'   
        template=template+'}'

        print(template)
        print('sdafadsfa')
        return template

