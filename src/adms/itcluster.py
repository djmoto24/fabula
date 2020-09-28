'''
Created on 8 июл. 2020 г.

@author: ladmin
'''
import subprocess
from srv.skeel import LayerFactorySkeel

from fabricio import docker, tasks

from srv.strategies import CommonStrategyForPhp
from fabric import  colors, api as fab
from srv.skeel import VolumeManager

class CustomProgStrategy(CommonStrategyForPhp):
        
    def initRepo(self, branch='master'):
        repo=self._element.initRepoForLayer(branch=branch)
        #repo=self._element._gitrepos.changeBranch('origin', repo, branch)
        return repo    
    
    #def fullcycle(self):
    #    self.prepare()
        
    #    self._element.push()
    #    fab.execute(
    #        self._element.upgrade,
    #        tag=tag,
    #        force=force,
    #        backup=backup,
    #        migrate=migrate,
    #    )

class AdmItcluster(LayerFactorySkeel):
    
    def buildPostgresWithDatabase(self):

        #self._element.option=('env',  ['CLUSTER_USER=moscluster', 
        #                       'CLUSTER_PASSWORD=Li2iR0wLa5', 
        #                       'CLUSTER_DB=moscluster', 
        #                       'POSTGRES_USER=postgres', 
        #                       'POSTGRES_PASSWORD=BozCh128Mer', 
        #                       'CUR_DUMP=mk.sql' ])
        self._element.opt=('env', ['PGDATA=/var/lib/postgresql-static/data'])
        self._element.opt=('network', ['demo_local'])  
        #self._element.option=('mount', ['type=volume,source=intervol,destination=/var/lib/postgresql/data,readonly=false']) 
        self._element.setService(service=docker.Container(
            name=self._element.imageTag,
            image=self._element.serviceTag,
            options=self._element.opt,
            )) 
        #self._element.options=opt
        pgDockerfile=self.dockerFactory.get_PostgresProvision(layer=self._element.layerPath, dbname='moscluster', dbuser='moscluster', dbpass='Li2iR0wLa5')
        self._element.add_dockerfile(pgDockerfile)
        
        #res=subprocess.run('/usr/bin/pg_dump -Fc --host=10.32.201.213 --username=moscluster  --schema-only --file=./tmp/mk.sql --dbname=moscluster', shell=True)
        #res=subprocess.Popen(['ls', '-la'])
        
        return self._element
    
    def makePostgres(self):
        self._element.opt=('network', ['demo'])
        self._element.opt=('mount', ['type=volume,source=intervol,destination=/var/lib/postgresql/data,readonly=false'])  
        self._element.setService(service=docker.Container(
            name=self._element.imageTag,
            image=self._element.serviceTag,
            options=self._element.opt,
            )) 
        
        return self._element
    
    def buildTraefic(self):
        #self._element.option=('network', ['efirmain'])
        
        #self._element.option=('command', ['--api', /entrypoint.sh traefik
        #                                  '--entrypoints=Name:http Address::80', 
        #                                  '--defaultentrypoints=http', 
        #                                  '--docker',
        #                                  '--docker.domain=docker-example.local',
        #                                  '--docker.watch'])
        #self._element.option=('volume', '/var/run/docker.sock:/var/run/docker.sock')
        #serviceName=self._element.myname+'_'+self._element.imageTag
        #serviceTag=self._element.imageTag
        #self._element.opt=('network', ['demo']) 
        self._element.setService(service=docker.Service(
            name=self._element.imageTag,
            image=self._element.serviceTag,
            options=self._element.opt,
            args="--api.insecure=true \
            --providers.docker=true \
            --providers.docker.swarmMode=true \
            --providers.docker.watch=true \
            --providers.docker.swarmModeRefreshSeconds=15s \
            --providers.docker.exposedbydefault=false \
            '--providers.docker.defaultRule=Host('local.me')' \
            --entrypoints.web.address=:80 \
            --api.dashboard=true"))
        
        return self._element
    
    def buildFpm(self):
        #options={
        #        'publish': ['9003:9000']
        #    }
        
        
        #self._element.option=('publish', ['9003:9000'])
        #self._element.option=('network', ['demo'])
        #self._element.option=('label', [ 'com.docker.lb.backend_mode=task',  
        #                               'com.docker.lb.hosts=demo.local'])
        firstVol=VolumeManager(role=self._element._role, source='vol1')
        firstVol.setDestination(destination='/usr/share/nginx/html')
        self._element.volumes=firstVol
        #self._element.option=('mount', ['type=volume,source=nfvol_1,destination=/usr/share/nginx/html,readonly=false'])
        dockererfile=self.dockerFactory.get_php73_fpmDictFile(layer=self._element.layerPath)
        self._element.add_dockerfile(dockererfile)
        #serviceName=self._element.myname+'_'+self._element.imageTag
        #serviceTag=os.path.join(self._element.registry, self._element.imageTag)
        self._element.setService(service=docker.Service(
            name=self._element.imageTag,
            image=self._element.serviceTag,
            options=self._element.opt,
            ))
        return self._element
            
    def buildLayerWithCustomSteps(self) -> None:
        pass

