import os, stat, re

from abc import ABC, abstractmethod, abstractproperty
from fabric import  colors, api as fab
from fabric import tasks as taskwrap
from fabricio.tasks import ImageBuildDockerTasks, DockerTasks, Tasks
from fabricio import docker, tasks
from fabric.decorators import task

from src.objectlib import DockerfileFactory, Dockerfile, Networker

from fabric.tasks import Task, WrappedCallableTask, get_task_details


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
    options={}
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
    def option(self):
        return self.options
    @option.setter
    def option(self, val):
        print(self.options)
        try:
            optname, value = val
        except ValueError:
            raise ValueError("Pass an iterable with two items")
        else:
            """ This will run only if no exception was raised """
            self.options[optname]=value
     
    @option.deleter
    def option(self, optname):
        del self.options[optname]
                
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
    
    #@abstractmethod     
    def runrepo(self):
        try:
            self._gitrepos.prepare(workdir=self.layerPath)
        except:
            print("Repo isn't initialized")  
    
    @fab.hosts()
    @fab.roles()
    @fab.task
    def dockerLogin(self):
        if self.dockerlogin:
            cmd='docker login '+self.registry
            fab.run(cmd)      
    
    @abstractmethod
    def hook(self):
        print("This is hook code")
   

class ExecStrategy(ABC):
    
    def __init__(self, element: Element):
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

class CommonStrategyForNginx(ExecStrategy):
    
    def prepare(self):
        self._element.hook()
        self._element.runrepo()
        self._element._dockerfileObj.buildfile()
        self._element.initservice() 
        fab.execute(self._element.dockerLogin)
    
    def fullcycle(self):
        #tag=None
        #force=False
        #backup=False
        #migrate=True
        
        self.prepare()
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
        
class CommonStrategy(ExecStrategy):
    
    def prepare(self):
        self._element.runrepo()
        self._element.hook()
        self._element._dockerfileObj.buildfile()
        self._element.initservice()
        #self._element.prepare() 
    
    def fullcycle(self):
        self.prepare()
        
        self._element.push()
        self._element.backup()
        self._element.pull()
        self._element.migrate()
        self._element.update()
        self._element.upgrade()
        self._element.deploy()
        
class ConstructStrategy(ExecStrategy):
    def prepare(self):
        self._element.hook()
        self._element.initservice()
        #fab.execute(self._element.dockerLogin)
        
    def fullcycle(self):
        self.prepare()
        self._element.deploy()

class CommonStrategyForPhp(ExecStrategy):
    
    def prepare(self):
        self._element.hook()
        self._element.runrepo()
        self._element._dockerfileObj.buildfile()
        self._element.initservice() 
    
    def fullcycle(self):    
        self.prepare()
        self._element.deploy()

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
    def layer(self, strategy: ExecStrategy):
        
        self.stack[strategy._element.imageTag]=strategy
        self._increment()
        
    def _increment(self):
        self.__index+=10
    
    @fab.hosts()
    @fab.roles()
    @fab.task    
    def compile_layers(self):
        
        print(self.stack)
        for item in self.stack.keys():
            self.stack[item].fullcycle()
    
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
        print(opt)
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
        print(fab.env.roledefs) 
    
    def appendDatabase(self, dbDump):
        pass
    
    #@abstractmethod            
    def hook(self):
        print('rewritd hook')

class LayerBuilder(ImageBuildDockerTasks, Tasks, Element):
    
    def __init__(self, role=['defrole'], 
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
        
    def initservice(self):
        super(LayerBuilder, self).__init__(self._service,
                                      build_path=self.serviceName,
                                      roles=self._role,
                                      registry=self.registry)
        fab.execute(self.dockerLogin)
    
    
    def hook(self):
        print('rewritd hook')
        

class LayerConstructor(DockerTasks, Element):

    def __init__(self, role=['defrole'], 
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
        
    def initservice(self):
        super(LayerConstructor, self).__init__(self._service,
                                               roles=self._role,
                                               registry=self.registry)
        fab.execute(self.dockerLogin)
             
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
        
    def customizeInifile(self, iniFileName):
        print(iniFileName)
             
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
        self._element.option=('network', ['efirmain'])
        
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
                                                        options=self._element.option,
                                                        args='--api.insecure=true --api.dashboard=true'))
        #self._element.setService(self.generator.serviceGenerator(layerName=serviceName, 
        #                                                         imageTag=serviceTag, 
        #                                                         opt=self._element.option))
        strategy=ConstructStrategy(self._element)
        return strategy

    def buildNginx(self):
        #self._element.option=('network', ['demo'])
        self._element.option=('publish', ['81:81'])
        dockererfile=self.dockerFactory.get_nginxCommonDictFile(layer=self._element.layerPath)
        self._element.add_dockerfile(dockererfile)
        self._element.setService(service=docker.Service(
            name=self._element.imageTag,
            image=self._element.serviceTag,
            options=self._element.option,
            ))
        
        strategy=CommonStrategyForNginx(self._element)
        
        return strategy
    def buildFpm(self):
        options={
                'publish': ['9003:9000']
            }
        #self._element.option=('publish', ['9003:9000'])
        self._element.option=('network', ['demo'])
        self._element.option=('label', [ 'com.docker.lb.backend_mode=task',  
                                        'com.docker.lb.hosts=demo.local'])
        phpDockererfile=self.dockerFactory.get_php73_fpmDictFile(layer=self._element.imageTag)
        self._element.add_dockerfile(phpDockererfile)
        opts=self._element.option
        #serviceName=self._element.myname+'_'+self._element.imageTag
        #serviceTag=os.path.join(self._element.registry, self._element.imageTag)
        self._element.setService(self.generator.serviceGenerator(layerName=self._element.serviceName, 
                                                                 imageTag=self._element.serviceTag, 
                                                                 opt=opts))
        strategy=CommonStrategyForPhp(self._element)
        return strategy

    def buildPostgresWithDatabase(self, dbDump) -> None:

        self._element.option=('env',  ['CLUSTER_USER=moscluster', 
                               'CLUSTER_PASSWORD=Li2iR0wLa5', 
                               'CLUSTER_DB=moscluster', 
                               'POSTGRES_USER=postgres', 
                               'POSTGRES_PASSWORD=BozCh128Mer', 
                               'CUR_DUMP=dump.sql' ])
        self._element.option=('network', ['demo'])    
        pgDockerfile=self.dockerFactory.get_Postgres96Dockerfile(layer=self._element.imageTag)
        self._element.add_dockerfile(pgDockerfile)
        self._element.appendDatabase(dbDump)
        opts=self._element.option
        serviceName=self._element.myname+'_'+self._element.imageTag
        serviceTag=os.path.join(self._element.registry, self._element.imageTag)
        self._element.setService(self.generator.serviceGenerator(layerName=serviceName, 
                                                                 imageTag=serviceTag, 
                                                                 opt=opts))
        strategy=CommonStrategy(self._element)
        return strategy


    
        
        
        
        
    
    
    

