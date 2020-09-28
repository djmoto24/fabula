'''
Created on 14 февр. 2020 г.

@author: ladmin
'''
from fabric import colors, api as fab
from dpath import util

from srv.skeel import BlackBox

from fabricio import  tasks #docker,

from srv.objectlib import gitworker

from srv.skeel import AdmDirector
from srv.skeel  import PostgresLayer, LayerBuilder, PhpFpm73Layer, LayerConstructor
from adms.itcluster import AdmItcluster, CustomProgStrategy
from srv.strategies import ConstructStrategy, CommonStrategyForNginx,\
    CommonStrategy

from srv.skeel import RoleManager, NetworkManager, VolumeManager
#from dockerfabric import tasks as docker


class ItCluster(tasks.Tasks, BlackBox):
    projectName='ItCluster'
    
    def __init__(self):
        #fab.env.roledefs.update(
        #    balancer=['user@staging.example.com'],
        #    web=['ladmin@127.0.0.1'],
        #    prod=['developer@10.32.201.213'],
        #    prod_postgres=['ladmin@127.0.0.1', 'developer@10.32.201.213']
        #    )
        balanser=RoleManager(['balanser'])
        balanser.adress=['user@staging.example.com']
        local=RoleManager(['local'])
        local.adress=['ladmin@127.0.0.1']
        prod=RoleManager(['prod']) 
        prod.adress=['developer@10.32.201.213']
        
        fab.env.roledefs.update(balanser=balanser,
                                local=['ladmin@127.0.0.1'],
                                prod=['developer@10.32.201.213'],
                                )
    
        
        demo_local=NetworkManager(netname='demo_local', driver='bridge')
        demo=NetworkManager(netname='demo', driver='overlay')
       
        #gitFpm=gitworker(git_rep='developer@10.32.201.213:/www/itcluster.srvdev.ru/personal/reliz.itcluster.srvdev.ru/.git', 
                        #keepath='/home/ladmin/workspace_cpp/fabula/rsa/id_ladm_rsa')
        #gitNginx=gitworker(git_rep='developer@10.32.201.213:/www/itcluster.srvdev.ru/personal/reliz.itcluster.srvdev.ru/.git', 
                        #keepath='/home/ladmin/workspace_cpp/fabula/rsa/id_ladmin_rsa')
        
        gitFpmItcluster=gitworker(git_rep='git@gitlab.srvdev.ru:itcluster/i.moscow.git', 
                        keepath='/home/ladmin/workspace_cpp/fabula/rsa/id_ladmin_rsa')
        
        #remoteDocker=docker.DockerClient(base_url='unix://var/run/docker.sock')
        
        
        director=AdmDirector()
        it_director=AdmItcluster()
        postgresInter=LayerBuilder(role=local, net=demo_local, dockerlogin=True, registry="reg-itcluster.srvdev.ru:5001", projectname='itcluster', imageTag='postgresinter')
        traefik=LayerConstructor(role=prod, net=demo, dockerlogin=True, registry="reg-itcluster.srvdev.ru:5001",  projectname='itcluster', imageTag='traefik', release="latest")
        nginx=LayerBuilder(role=prod, net=demo, dockerlogin=True, registry="reg-itcluster.srvdev.ru:5001", projectname='itcluster', imageTag='nginx', release="latest")
        
        fpm=LayerBuilder(role=prod, net=demo, dockerlogin=True, registry="reg-itcluster.srvdev.ru:5001", projectname='itcluster', imageTag='fpm74')
        
        #intermed=LayerConstructor(role=['prod'], dockerlogin=True, registry="reg-itcluster.srvdev.ru:5001",  projectname='itcluster', imageTag='itsthenetwork/nfs-server-alpine', release="latest")
        
        #nginx.add_git_repo(gitFpmItcluster)
        fpm.add_git_repo(gitFpmItcluster)
        
        
        director.builder=nginx
        it_director.builder=fpm
        
        self.nginx=director.buildNginx()
        self.fpm=it_director.buildFpm()
        
        it_director.builder=traefik
        self.traefik=it_director.buildTraefic()
        
        postgresInter.opt=('publish', ['54320:5432'])
        it_director.builder=postgresInter
        self.postgresInter=it_director.buildPostgresWithDatabase()
        
    @fab.hosts()
    @fab.roles()
    @fab.task 
    def packStrategy(self):
        '''
        Пример упаковки контейнеров в стратегии обработки.
        Стратегии включают в себя типовые алгоритмы и дают возможность писать добавлять свои, 
        алгоритмы для интерфейсных функций, объявленных в абстрактном классе-родителе
        '''
        
        traefikStrat=ConstructStrategy(self.traefik)
        fpmStrat=CustomProgStrategy(self.fpm)
        nginxStrat=CommonStrategyForNginx(self.nginx)
        postStratInter=CommonStrategy(self.postgresInter)
        
        self.layer=traefikStrat
        self.layer=postStratInter
        
        self.layer=fpmStrat
        self.layer=nginxStrat
  
        
    @fab.hosts()
    @fab.roles()
    @fab.task 
    def rebuildNginx(self):
        '''
        пересборка одного контейнера
        '''
        #repo=self.nginx.initRepoForLayer('rolesystem')
        nginxStrat=CommonStrategyForNginx(self.nginx)
        nginxStrat.fullcycle()
        
    @fab.hosts()
    @fab.roles()
    @fab.task 
    def rebuildFpm(self):
        '''
        пересборка одного контейнера
        '''
        self.stack['fpm74'].fullcycle()
    
    @fab.hosts()
    @fab.roles()
    @fab.task 
    def rebuildPostgres(self):
        '''
        пересборка одного контейнера
        '''
        self.stack['postgresinter'].fullcycle()
        
    @fab.hosts()
    @fab.roles()
    @fab.task 
    def migratePostgres(self):
        '''
        пересборка одного контейнера
        '''
        prod=RoleManager(['prod']) 
        prod.adress=['developer@10.32.201.213']
        tag='V3'
        demo=NetworkManager(netname='demo', driver='overlay')
        self.stack['postgresinter']._element.deleteOpt('publish')
        self.stack['postgresinter']._element.commit(tag)
        self.stack['postgresinter']._element.changeRole(role=prod)
        self.stack['postgresinter']._element.network=demo
        self.stack['postgresinter']._element.convertToService(tag=tag)
        self.stack['postgresinter'].migrate(tag=tag)
    @fab.hosts()
    @fab.roles()
    @fab.task 
    def branchConf(self, branch='master'):
        '''
        Пример конфигурирования репозитория, перед сборкой
        '''
        
        repo=self.stack['fpm74'].initRepo(branch)
        #repo=self.stack['nginx'].initRepo(branch)
        # Любые действия с репозиторием....
     
    @fab.hosts()
    @fab.roles()
    @fab.task 
    def addEnv(self):
        '''
        Пример добавления файла в сценарий сборки
        '''
        self.stack['fpm74']._element._dockerfileObj.COPY('fpmfiles/env', '/usr/share/nginx/html/.env', 201)
        self.stack['fpm74']._element._dockerfileObj.COPY('fpmfiles/env.local', '/usr/share/nginx/html/.env.local', 202)
        self.stack['fpm74']._element._dockerfileObj.COPY('fpmfiles/composer', '/usr/share/nginx/html/composer', 203)
        self.stack['fpm74']._element._dockerfileObj.add_STRING('RUN echo \'DATABASE_URL=pgsql://moscluster:Li2iR0wLa5@postgresinter:5432/moscluster\' >> /usr/share/nginx/html/.env.local', 361)          
    @fab.hosts()
    @fab.roles()
    @fab.task 
    def compile(self):
        '''
        Деплой тестовой инфраструктуры
        '''
        self.compile_layers()     
    @fab.hosts()
    @fab.roles()
    @fab.task 
    def applay_args(self):
        '''
        Применение аргументов сервисов
        '''

        self.stack['traefik']._element._service.args='--api.insecure=true --api.dashboard=true --providers.docker=true'
        #option=('args', ' --api.insecure=true --api.dashboard=true --providers.docker=true --providers.docker.swarmMode=true --providers.docker.exposedbydefault=false --entrypoints.http.address=:80')
        self.compile_layers()

class Efir(BlackBox, tasks.Tasks):
    projectName='efir'
    
    def __init__(self):
        fab.env.roledefs.update(
            balancer=['user@staging.example.com'],
            web=['ladmin@127.0.0.1'],
            prod=['root@ru-sp1.efir.io']
            )
        gitex=gitworker(git_rep='git@bitbucket.org:denvvii/efir.git', 
                        wrapper='rsa/wrap_developer_127.0.0.1.sh')
        director=AdmDirector()
        
        nginx=LayerBuilder(role=['prod'], projectname='itcluster', imageTag='nginx' )
        #traefic=LayerConstructor(role=['web'], name=self.projectName, imageTag='traefik')
        
        #fpm=PhpFpm73Layer(role=['web'], name=self.projectName+'fpm')
        
        nginx.add_git_repo(gitex)
        
        director.builder=nginx
        ngStrat=director.buildNginx()
        self.layer=ngStrat
        
        #director.builder=traefic
        #traeficStrat=director.buildTraeficForEfir()
        #self.layer=traeficStrat
       
        
        
    @fab.hosts()
    @fab.roles()
    @fab.task 
    def compile(self):
        '''
        Деплой тестовой инфраструктуры
        '''       
        self.compile_layers()
        
        
    @fab.hosts()
    @fab.roles()
    @fab.task 
    def applay_args(self):
        '''
        Применение аргументов сервисов
        '''

        self.stack['traefik']._element._service.args='--api.insecure=true --api.dashboard=true --providers.docker=true'
        #option=('args', ' --api.insecure=true --api.dashboard=true --providers.docker=true --providers.docker.swarmMode=true --providers.docker.exposedbydefault=false --entrypoints.http.address=:80')
        self.compile_layers()
    