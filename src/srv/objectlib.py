'''
Created on 30 июл. 2020 г.

@author: ladmin
'''

import os, stat, shutil, re, sys
import json
from fabric import  colors, api as fab
from git import Repo
from git import Git
from git.exc import GitCommandError
from fabric2 import Connection
#from _ast import Try
    

class Dockerfile():
    
    _dockerfile='Dockerfile'
    destFile='Dockerfile'
    _file=None
    _w_dir='/tmp'
    dockerfilePath=os.path.join(_w_dir, _dockerfile)
    
    def __init__(self, layerPath):
        self.layerPath=layerPath
        self.reset()
        #self.open()
        self._index=10
        
    
    def open(self):
        
        try:
            os.remove(self.dockerfilePath)
            self._file = open(self.dockerfilePath, 'w')
            # Do something with the file
        except IOError:
            self._file = open(self.dockerfilePath, 'w')
    
    def close(self):
        self._file.close()
        
    def reset(self):
        self.dockerfile={}
    
    def _increment(self):
        self._index+=10
        
    def buildfile(self):
        dest=os.path.join(self.layerPath, self.destFile)
        file=None
        try:
            os.remove(dest)
            file = open(dest, 'w')
            # Do something with the file
        except IOError:
            file = open(dest, 'w') 
           
        for key in sorted(self.dockerfile.keys()):
            file.write(self.dockerfile[key]+'\n')
        
        file.close()
        print(self.layerPath)
    
    def copyall(self, src, dst, symlinks=False, ignore=None):
        
        if os.path.exists(dst):
            if os.path.isfile(dst) or os.path.islink(dst):
                os.remove(dst)
            else:
                shutil.rmtree(dst, ignore_errors=True, onerror=True)   
        if os.path.isdir(src):
            shutil.copytree(src, dst, symlinks, ignore)
        else:
            shutil.copy2(src, dst)
    
    def add_STRING(self, str_content, index=None):  
        if index is not None:
            self.dockerfile[index]=str_content
        else: 
            self.dockerfile[self._index]=str_content
        self._increment()
        self.ADD.__name__
    def FROM(self, str_content):
        self._file.write("FROM "+str_content+'\n')   
    def RUN(self, str_content):
        self._file.write("RUN "+str_content+'\n')
    def ADD(self, source, destination, index=None):
        if index is not None:
            self.dockerfile[index]=self.ADD.__name__+' '+source+' '+destination
        else:
            self.dockerfile[self._index]=self.ADD.__name__+' '+source+' '+destination
        #print(os.getcwd())
        os.makedirs(os.path.dirname(os.path.join(self.layerPath, source)), stat.S_IRWXU, exist_ok=True)
        self.copyall(source, os.path.join(self.layerPath, source))
        self._increment()
    def EXPOSE(self, str_content):
        self._file.write("EXPOSE "+str_content+'\n')
    def VOLUME(self, str_content):
        self._file.write("VOLUME "+str_content+'\n')
    def CMD(self, str_content):
        self._file.write("CMD "+str_content+'\n')
    def WORKDIR(self, str_content):
        self._file.write("WORKDIR "+str_content+'\n')
    def COPY(self, source, destination, index=None):
        if index is not None:
            self.dockerfile[index]=self.COPY.__name__+' '+source+' '+destination
        else:
            self.dockerfile[self._index]=self.COPY.__name__+' '+source+' '+destination
            
        #print(os.path.join(self.layerPath, source))
        os.makedirs(os.path.dirname(os.path.join(self.layerPath, source)), stat.S_IRWXU, exist_ok=True)
        self.copyall(source, os.path.join(self.layerPath, source))
        self._increment()


class gitworker(object):
    '''
    Класс, реализующий доступ к репозиторию проекта
    '''
    gitrep=0

    def __init__(self, git_rep, keepath=os.getcwd()+'id_deployment_key'):
        '''
        Constructor
        '''
        'ladmin@127.0.0.1:/git/itcluster/.git'
        self.gitrep=git_rep
        self.keepath=keepath
        #self.workdir='/home/ladmin/workspace_cpp/fabrica'   
        
    
    def prepareRepo(self, workdir, cur_branch='master'):     
        try:
            cur_repo = Repo(os.path.join(workdir, 'html'))
            assert not cur_repo.bare
        except Exception as exRepo:
            ssh_cmd='ssh -i '+self.keepath
            #ssh_executable = os.path.join(keepath, self.wrapper)
            print(exRepo)
            #with  Git().custom_environment(GIT_SSH=ssh_executable):
            try:
                with  Git().custom_environment(GIT_SSH_COMMAND=ssh_cmd):
                    cur_repo = Repo.clone_from(self.gitrep, os.path.join(workdir, 'html'), branch=cur_branch)        
            except Exception as exGit:
                print(exGit)
        assert not cur_repo.is_dirty()
        return cur_repo

    def changeBranch(self, repo, origin='origin', branch='master'):
        try:
            repo.git.checkout(branch)
            origin=repo.remote(origin)
            res=origin.pull(branch)
        except Exception as ex:
            print(ex)
        return repo
        
    def getRepo(self, workdir, cur_branch):
        repo=self.prepareRepo(workdir)
        try:
            self.changeBranch(repo=repo, branch=cur_branch)      
        except GitCommandError as ex:
            print(ex)
            raise SystemExit(0)
        return repo

class Networker():
    def __init__(self, netname):
        self._netname=netname
        try:
            inspectStr='docker network inspect '+self._netname
            ret = fab.run(inspectStr)
            self.net_param=json.loads(ret)[0]
            #name = net_param.get("Name")
        except:
            print("Netname not defined. Creating new nerwork ")
            
    def getRelateIpList(self, filter="bridge"):
        containers=self.net_param['Containers']
        iplist={}
        for cont in containers.keys():
            container=containers[cont]
            for param in container.keys():
                if re.match(filter, container[param]) is not None:
                    iplist[container['Name']]=container['IPv4Address'][0:-3]
        
        return iplist