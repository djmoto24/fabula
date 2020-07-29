'''
Created on 14 февр. 2020 г.

@author: ladmin
'''
from fabric import colors, api as fab
from dpath import util

from src.skeel import BlackBox

from fabricio import docker, tasks

from src.objectlib import gitworker

from src.skeel import AdmDirector
from src.skeel  import PostgresLayer, LayerBuilder, PhpFpm73Layer, LayerConstructor
from src.adms.itcluster import AdmItcluster

from dockerfabric import tasks as docker


class ItCluster(tasks.Tasks, BlackBox):
    projectName='ItCluster'
    
    def __init__(self):
        fab.env.roledefs.update(
            balancer=['user@staging.example.com'],
            web=['ladmin@127.0.0.1'],
            prod=['developer@10.32.201.213']
            )
        gitex=gitworker(git_rep='developer@10.32.201.213:/www/itcluster.srvdev.ru/personal/reliz.itcluster.srvdev.ru/.git', 
                        wrapper='rsa/wrap_developer_127.0.0.1.sh')
        
        #fab.env.docker_base_url = 'tcp://127.0.0.1:8000'
        #fab.env.docker_tunnel_local_port = 22024  
        #docker.version()
        
        director=AdmDirector()
        it_director=AdmItcluster()
        
        traefic=LayerConstructor(role=['prod'], dockerlogin=True, registry="reg-itcluster.srvdev.ru:5001",  projectname='itcluster', imageTag='traefik', release="latest")
        nginx=LayerBuilder(role=['prod'], dockerlogin=True, registry="reg-itcluster.srvdev.ru:5001", projectname='itcluster', imageTag='nginx')
        #nginx.dockerLogin()
        
        fpm=LayerBuilder(role=['prod'], dockerlogin=True, registry="reg-itcluster.srvdev.ru:5001", projectname='itcluster', imageTag='fpm74')
        
        nginx.add_git_repo(gitex)
        fpm.add_git_repo(gitex)
        
        
        director.builder=nginx
        it_director.builder=fpm
        
        ngStrat=director.buildNginx()
        fpStart=it_director.buildFpm()
        
        it_director.builder=traefic
        traefikStrat=it_director.buildTraefic()
        
        self.layer=traefikStrat
        self.layer=ngStrat
        self.layer=fpStart
        
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
    