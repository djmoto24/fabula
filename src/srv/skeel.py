'''
Created on 30 июл. 2020 г.

@author: ladmin
'''

import os, stat, re

from abc import ABC, abstractmethod, abstractproperty
from fabric import  colors, api as fab
#from fabric import tasks as taskwrap
from fabricio.tasks import ImageBuildDockerTasks, DockerTasks, Tasks
from fabricio import docker, tasks



from srv.objectlib import Dockerfile, Networker
from srv.dockerfiles import DockerfileFactory

from fabric.tasks import Task, WrappedCallableTask, get_task_details

from fabric2 import SerialGroup as Group
from fabric2 import Connection

def fname(function_to_decorate):
    def the_wrapper_around_the_original_function():
        print("Я - код, который отработает до вызова функции")
        function_to_decorate() # Сама функция
        print("А я - код, срабатывающий после")
    return the_wrapper_around_the_original_function

class Element(ABC):
    
    _dockerfileObj=Dockerfile('emptylayer')
    registry=''
    _service=None
    
    dockerlogin=False
    
    @abstractmethod
    def initservice(self):
        pass
    
    def prepareDir(self):
        try:
            os.mkdir(self.layerPath)
            os.chmod(self.layerPath, stat.S_IRWXU, follow_symlinks=True)
        except OSError:
            print ("Создать директорию %s не удалось" % self.layerPath)
        else:
            print ("Успешно создана директория %s " % self.layerPath)
    
    @property
    def opt(self):
        return self.options.copy()
    @opt.setter
    def opt(self, val):
        if 'options' not in self.__dict__:
            self.options={}
        
        try:
            optname, value = val
        except ValueError:
            raise ValueError("Pass an iterable with two items")
        else:
            """ This will run only if no exception was raised """
            self.options[optname]=value
        
    def deleteOpt(self, optname):
        if 'options' not in self.__dict__:
            self.options={}
        try:
            del self.options[optname]
        except Exception as ex:
            print(ex)
            print('Value {optname} is not delete'.format(optname=optname))
    @property
    def network(self):
        return self.__net
    @network.setter
    def network(self, net):
        net.setRole(self._role)
        self.__net=net
        self.opt=('network', [self.__net.netname])
        
    @property
    def volumes(self):
        return  self.__vols
    @volumes.setter
    def volumes(self, vol):
        self.__vols={}
        self.__vols[vol.source]=vol
        self.opt=('mount', vol.generateVolString())
    
    def setService(self, service):
        self._service=service
    
    def add_git_repo(self, gitrepos):       
        self._gitrepos=gitrepos
       
    #@abstractmethod    
    def add_dockerfile(self, dockerfileObj):
        self._dockerfileObj=dockerfileObj
    #@abstractmethod    
    def applay_dockerfile(self):
        self._dockerfileObj.passFileToProject(self.layerPath)
    
    def changeRole(self, role):
        self._role=role
        for obj in vars(self).values():
            if isinstance(obj, WrappedCallableTask):
                obj.roles=role
    
    #@abstractmethod     
    def initRepoForLayer(self, branch='master'):
        self.prepareDir()
        try:
            rep=self._gitrepos.getRepo(workdir=self.layerPath, cur_branch=branch)
        except Exception as ex:
            print(ex)
        return rep
    
    def convertToService(self, tag='v1'):
        service=docker.Service(
            name=self.imageTag,
            image=self.serviceName+':'+tag,
            options=self.opt,
            )
        self.setService(service)
    
    @fab.hosts()
    @fab.roles()
    @fab.task    
    def updateFromImage(self, tag=None, force=False):
        """
        update service use prebiuild image
        """
        fab.execute(self.pull, tag=tag)
        fab.execute(self.update, tag=tag, force=force)
         
    def dockerLogin(self):
        if self.dockerlogin:
            cmd='docker login '+self.registry
            self._role.run(cmd)
              
    @fab.hosts()
    @fab.roles()
    @fab.task
    def commit_task(self, tag='v1'):
        cmd='docker commit {ID} {newServiceTag}'.format(ID=self.service.info['Id'], 
                                                        newServiceTag=self.registry+'/'+self.serviceName+':'+tag)
        fab.run(cmd)
        self.push(tag=tag)
        fab.env.host=None
        fab.env.host_string=None
        #fab.env.passwords=None
    
    @abstractmethod
    def hook(self):
        print("This is hook code")
        
    def getrole(self):
        return self._role
    
class Manager(object):
    def __init__(self):
        pass
        

class NetworkManager(Manager):
    def __init__(self, netname, role=False,  driver='bridge'):
        self.role=role
        self.netname=netname
        self.driver=driver
    def setRole(self, role):
        self.role=role
    def createNetwork(self):
        res=self.role.execute(self._createNetwork)
        return res
    
    def _createNetwork(self, connection):
        try:
            net=connection.networks.get(self.netname)
            print("Network {name} exist".format(name=net))
        except Exception as Ex:
            res=connection.networks.create(self.netname, driver=self.driver)
            res
        return False
        
    def update(self):
        print("updating network")
        self.createNetwork()

class RoleManager(list):
    def __new__(cls, role):
        cls.role=role
        cls.portIndex=23750
        return super().__new__(cls)
    #def __init__(self, role, addr):
        #self.role=role
        #self.addr=addr
    def setAddr(self, addr):
        self.addr=addr    
    
    def execute(self, callFunc):
        
        import paramiko
        from docker import DockerClient
        from sshtunnel import SSHTunnelForwarder
        import time

        for host in self.adress:
            user=host.split('@', 1)[0]
            addr=host.split('@', 1)[1]
            port=self.localConnectionPort
            forward=SSHTunnelForwarder((addr, 22), 
                                ssh_username=user, 
                                ssh_pkey="/var/ssh/rsa_key", 
                                ssh_private_key_password="secret", 
                                remote_bind_address=(addr, 2375), 
                                local_bind_address=('127.0.0.1', port))
            forward.start()
            time.sleep(3)
            dockerConection=DockerClient('tcp://127.0.0.1:{port}'.format(port=port))
            res=callFunc(dockerConection)
            dockerConection.close()
            del dockerConection
            forward.stop()
        return res
    
    @property
    def localConnectionPort(self):
        port=self.portIndex
        self.portIndex+=1
        return port
    
    def getConnections(self):
        dockerConections={}
        for host in self.adress:
            dockerConections[host]=self.openDockerConnection(host=host)
        return dockerConections
    @property
    def adress(self):
        return self.addr
    @adress.setter
    def adress(self, addr):
        self.addr=addr
        
    @property
    def roles(self):
        return self.role
    @roles.setter
    def roles(self, rolename):
        self.role=rolename
        #self.updateGlobalRoles(rolename)
    #@role.deleter
    #def roles(self, rolename):
    #    del self.role_list.remove(rolename)    
    def run(self, arg):
        for host in self.adress:
            result = Connection(host).run(arg, pty=True)
            print("{}: {}".format(host, result.stdout.strip()))
    
    
    
class VolumeManager(Manager):
    def __init__(self, role, typeVol='volume', driver='local', source='defvol', options='readonly=false'):
        self.role=role
        self.driver=driver
        self.source=source
        self.typeVol=typeVol
        self.options=options
        self.template='type={type},source={source},destination={destination},{options}'
    def setDestination(self, destination):
        self.destination=destination
    def setSource(self, source):
        self.source=source
    def setType(self, typeVol):
        self.typeVol=typeVol
    def setAditionalOpt(self, options):
        self.options=options
    
    def update(self):
        res=self.role.execute(self._create)
        return res
    
    def _create(self, connection):
        try:
            vol=connection.volumes.get(self.source)
            print("Volume {name} exist".format(name=vol))
        except Exception as Ex:
            res=connection.volumes.create(self.source, driver=self.driver)
            res
        return False
    
    def generateVolString(self):
        opt=self.template.format(type=self.typeVol, source=self.source, destination=self.destination, options=self.options)
        return [opt]
        


class BlackBox(ABC):
    '''
    classdocs
    '''
    stack={}
    __index=0
    
    projectName=None
    
    def __init__(self):
        '''
        Constructor
        '''
        pass
    #@abstractmethod    
    #def build_layer(self) -> None:
    #    pass
    
    @property
    def layer(self):
        return self.list
    
    @layer.setter
    def layer(self, strategy):
        
        self.stack[strategy._element.imageTag]=strategy
        self._increment()
        
    def _increment(self):
        self.__index+=10
    
    @fab.hosts()
    @fab.roles()
    @fab.task    
    def compile_layers(self):
        for item in self.stack.keys():
            self.stack[item].fullcycle()
    @fab.hosts()
    @fab.roles()
    @fab.task    
    def initAllRepo(self):
        for item in self.stack.keys():
            self.stack[item]._element.runrepo()
    
    @fab.hosts()
    @fab.roles()
    @fab.task    
    def push_layers(self):
        print('==== PUSH ====')


class CommonLayers():
    '''
    Класс - библиотека уровней
    '''
    
    def __init__(self):
        print("I am called")
        
    def serviceGeneratorPriv(self, layerName,  opt):
        service=docker.Service(
            name=layerName,
            image='127.0.0.1:5000/'+layerName,
            options=opt,
            )
        return service
    
    def serviceGenerator(self, layerName, imageTag, opt):
        print(layerName)
        service=docker.Service(
            name=layerName,
            image=imageTag,
            options=opt,
            
            )
        return service
    
    def pg_serv(self, seed='_seed', projectId='mybr'):
        service=docker.Service(
            name='pg_alldump'+seed,
            image='pg_alldump'+seed,
            options={
                'publish': ['54324:5432'],
                'network': [projectId],
                'env':  ['CLUSTER_USER=moscluster', 'CLUSTER_PASSWORD=Li2iR0wLa5', 'CLUSTER_DB=moscluster', 'POSTGRES_USER=postgres', 'POSTGRES_PASSWORD=BozCh128Mer', 'CUR_DUMP=dump.sql'],
                },
            )
        return service
    
    def nginx_serv(self, seed='_seed', projectId='mybr'):
        
        service=docker.Service(
            name='nginx'+seed,
            image='nginx'+seed,
            options={
                    #'publish': ['81:81'],
                    'volume': '/media:/media',
                    'network': [projectId],
                    },
            )
        #hosts=['root@127.0.0.1'],
        #roles=['web'],
        #registry=reg,
        #build_path='/home/ladmin/workspace_cpp/fabrica/nginx',
        return service
    
    def fpm73_serv(self, seed='_seed', projectId='mybr'):
        
        service=docker.Service(
            name='phpfpm73'+seed,
            image='phpfpm73'+seed,
            options={
                #'publish': ['9003:9000'],
                'network': [projectId],
                },
            )
        return service
    
    def webbuild(self, reg='127.0.0.1:5000'):
        Webprod = tasks.ImageBuildDockerTasks(
            service=docker.Container(
                name='base',
                image='app',
                ),
            roles=['web'],
            registry=reg,
            build_path='/home/ladmin/workspace_cpp/fabrica/nginx',
            )
        return Webprod
    
    def web(self, reg='127.0.0.1:5000'):
        Web = tasks.DockerTasks(
            service=docker.Container(
                name='web',
                image='127.0.0.1:5000/app',
                options={
                    'publish': ['81:81'],
                    'volume': '/media:/media',
                    },
                ),
            registry=reg,
            roles=['web'],
            #hosts=['root@127.0.0.1'],
            #account="ladmin"
            )
        return Web
    
    def phpfpm(self, reg='127.0.0.1:5000'):
        PhpFpm = tasks.ImageBuildDockerTasks(
        service=docker.Container(
            name='phpfpm',
            image='fpm',
            options={
                'publish': ['9000:9000'],
                'link': ['fpm'],
            },
        ),
        registry=reg,
        build_path='/home/ladmin/workspace_cpp/fabrica/php-fpm',
        roles=['phpfpm'],
        )
        
        return PhpFpm
    

class PostgresLayer(ImageBuildDockerTasks, Element):
    options={
                'publish': ['5432:5432'],
                'network': ['bridge'],
                }
    def __init__(self, role=['defrole'], registry='', name='testproj', imageTag='helloworld' , release=':latest'):
        Element.__init__(role, registry, name, imageTag, release)
    
    def initservice(self):
        super(PostgresLayer, self).__init__(self._service,
                                      build_path=self.layerPath,
                                      roles=self._role,
                                      registry=self.registry) 
    
    def appendDatabase(self, dbDump):
        pass
    
    #@abstractmethod            
    def hook(self):
        print('rewritd hook')

class LayerBuilder(ImageBuildDockerTasks, Tasks, Element):
    
    def __init__(self,
                net='network',
                role=['defrole'], 
                dockerlogin=False, registry='',
                projectname='testproj', 
                imageTag='unitname' , 
                release='latest'):
          
        self.dockerlogin=dockerlogin
        self.myname=projectname
        self.registry=registry
        self.imageTag=imageTag
        self.serviceName=projectname+'/'+imageTag
        self.serviceTag=projectname+'/'+imageTag+':'+release
        self.layerPath=os.path.join(os.getcwd(), self.serviceName)
        self._role=role
        self.network=net
        self.destroy = self.DestroyTask(tasks=self)
        
        
    def initservice(self):
        super(LayerBuilder, self).__init__(self._service,
                                      build_path=self.serviceName,
                                      roles=self._role,
                                      registry=self.registry,
                                      destroy_command=True)
        self.dockerLogin()
    
        
    def commit(self, tag='v1'):
        fab.execute(self.commit_task, tag)

    def hook(self):
        print('rewritd hook')
        
    #@fab.hosts()
    #@fab.roles()
    #@fab.task
    #def deploy(self, tag=None, force=False, backup=False, migrate=True):
    #    """
    #    deploy service (prepare -> push -> backup -> pull -> migrate -> update)
    #    """
    #    self.prepare(tag=tag)
    #    self.push(tag=tag)
    #    self.registry
    #    fab.execute(
    #        self.migrate,
    #        tag=tag,
    #        #force=False,
    #        #backup=False,
    #        #migrate=True,
    #    )
        

class LayerConstructor(DockerTasks, Element):

    def __init__(self,
                net='network',
                role=['defrole'], 
                dockerlogin=False, registry='',
                projectname='testproj', 
                imageTag='unitname' , 
                release='latest'):
        self.dockerlogin=dockerlogin
        self.myname=projectname
        self.registry=registry
        self.imageTag=imageTag
        self.serviceName=projectname+'/'+imageTag
        self.serviceTag=imageTag+':'+release
        self.layerPath=os.path.join(os.getcwd(), self.serviceName)
        self._role=role
        self.network=net
        self.destroy = self.DestroyTask(tasks=self)
    
        
    def initservice(self):
        super(LayerConstructor, self).__init__(self._service,
                                               roles=self._role,
                                               registry=self.registry)
        self.dockerLogin()
             
    def hook(self):
        print('rewritd hook')

class PhpFpm73Layer(ImageBuildDockerTasks, Element):

    options={
                'publish': ['9003:9000']
            }
           
    def initservice(self):
        super(PhpFpm73Layer, self).__init__(self._service,
                                      build_path=self.layerPath,
                                      roles=self._role,
                                      registry=self.registry)
        print(fab.env.roledefs)  
             
    def hook(self):
        print('rewritd hook')        

class LayerFactorySkeel(ABC):
    dockerFactory=DockerfileFactory()
    generator=CommonLayers()
    
    def __init__(self) -> None:
        self._element = None
        self.__index=0
        
        
    def reset(self):
        self._element=None
    def __increment(self):
        self.__index+=1
    
    @property
    def builder(self) -> Element:
        return self._element

    @builder.setter
    def builder(self, element: Element) -> None:
        """
        Директор работает с любым экземпляром строителя, который передаётся ему
        клиентским кодом. Таким образом, клиентский код может изменить конечный
        тип вновь собираемого продукта.
        """
        self._element = element

    """
    Директор может строить несколько вариаций продукта, используя одинаковые
    шаги построения.
    """
    
    @abstractmethod
    def buildLayerWithCustomSteps(self) -> None:
        pass

class AdmDirector(LayerFactorySkeel):
    
        
    def __init__(self):
        pass
 
    def buildLayerWithCustomSteps(self):
        pass

    def buildTraeficForEfir(self):
        self._element.opt=('network', ['efirmain'])
        
        #self._element.option=('command', ['--api', /entrypoint.sh traefik
        #                                  '--entrypoints=Name:http Address::80', 
        #                                  '--defaultentrypoints=http', 
        #                                  '--docker',
        #                                  '--docker.domain=docker-example.local',
        #                                  '--docker.watch'])
        #self._element.option=('volume', '/var/run/docker.sock:/var/run/docker.sock')
        #serviceName=self._element.myname+'_'+self._element.imageTag
        #serviceTag=self._element.imageTag
        self._element.setService(service=docker.Service(name=self._element.serviceName,
                                                        image=self._element.fullTag,
                                                        options=self._element.opt,
                                                        args='--api.insecure=true --api.dashboard=true'))
        #self._element.setService(self.generator.serviceGenerator(layerName=serviceName, 
        #                                                         imageTag=serviceTag, 
        #                                                         opt=self._element.option))
        return self._element

    def buildNginx(self):
        self._element.opt=('publish', ['81:80'])
        #self._element.net=NetworkManager(role=self._element._role, netname='demo', driver='local')
        #self._element.option=('network', ['demo'])
        firstVol=VolumeManager(role=self._element._role, source='vol1')
        firstVol.setDestination(destination='/usr/share/nginx/html')
        self._element.volumes=firstVol
        #self._element.option=('mount', ['type=volume,source=nfvol_1,destination=/usr/share/nginx/html,readonly=false'])
        dockererfile=self.dockerFactory.get_nginxCommonDictFile(layer=self._element.layerPath)
        self._element.add_dockerfile(dockererfile)
        self._element.setService(service=docker.Service(
            name=self._element.imageTag,
            image=self._element.serviceTag,
            options=self._element.opt,
            ))
        
        return self._element
        
    def buildFpm(self):
        #options={
        #        'publish': ['9003:9000']
        #    }
        self._element.opt=('publish', ['9003:9000'])
        self._element.opt=('network', ['demo'])
        self._element.opt=('label', [ 'com.docker.lb.backend_mode=task',  
                                        'com.docker.lb.hosts=demo.local'])
        phpDockererfile=self.dockerFactory.get_php73_fpmDictFile(layer=self._element.imageTag)
        self._element.add_dockerfile(phpDockererfile)
        opts=self._element.opt
        #serviceName=self._element.myname+'_'+self._element.imageTag
        #serviceTag=os.path.join(self._element.registry, self._element.imageTag)
        self._element.setService(self.generator.serviceGenerator(layerName=self._element.serviceName, 
                                                                 imageTag=self._element.serviceTag, 
                                                                 opt=opts))
        return self._element

