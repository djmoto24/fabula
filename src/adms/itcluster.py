'''
Created on 8 июл. 2020 г.

@author: ladmin
'''

from src.skeel import LayerFactorySkeel
from src.skeel import CommonStrategyForPhp, ConstructStrategy
from fabricio import docker, tasks

class AdmItcluster(LayerFactorySkeel):
    
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
        self._element.setService(service=docker.Service(
            name=self._element.imageTag,
            image=self._element.serviceTag,
            options=self._element.option,
            args="--api.insecure=true \
            --providers.docker=true \
            --providers.docker.swarmMode=true \
            --providers.docker.watch=true \
            --providers.docker.swarmModeRefreshSeconds=15s \
            --providers.docker.exposedbydefault=false \
            '--providers.docker.defaultRule=Host('local.me')' \
            --entrypoints.web.address=:80 \
            --api.dashboard=true"))
        
        strategy=ConstructStrategy(self._element)
        return strategy
    
    def buildFpm(self):
        options={
                'publish': ['9003:9000']
            }
        #self._element.option=('publish', ['9003:9000'])
        #self._element.option=('network', ['demo'])
        #self._element.option=('label', [ 'com.docker.lb.backend_mode=task',  
        #                               'com.docker.lb.hosts=demo.local'])
        dockererfile=self.dockerFactory.get_php73_fpmDictFile(layer=self._element.layerPath)
        self._element.add_dockerfile(dockererfile)
        opts=self._element.option
        #serviceName=self._element.myname+'_'+self._element.imageTag
        #serviceTag=os.path.join(self._element.registry, self._element.imageTag)
        self._element.setService(service=docker.Service(
            name=self._element.imageTag,
            image=self._element.serviceTag,
            options=self._element.option,
            ))
        strategy=CommonStrategyForPhp(self._element)
        return strategy
    
    def buildLayerWithCustomSteps(self) -> None:
        pass

