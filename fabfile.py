'''
Created on 5 мар. 2020 г.

@author: ladmin
'''

from fabricio import docker, tasks
from projects import Efir, ItCluster
from _ast import arguments
#from compose.cli import command

web = tasks.DockerTasks(
    service=docker.Service(
        name='traefik',
        image='traefik',
        command='--api',
        options={
            #'publish': ['81:81'],
            #'volume': '/media:/media',
        },
    ),
    registry='127.0.0.1:5000',
    #roles=['web'],
    hosts=['ladmin@127.0.0.1'],
    #account="ladmin"
    )
            
#DT=ItCluster()

if __name__ == '__main__':
    
    inst=ItCluster()
    inst.compile()
    #inst.applay_args(something='applay')
    print("hahqa")


    
    