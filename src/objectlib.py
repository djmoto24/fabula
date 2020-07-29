'''
Created on 14 февр. 2020 г.

@author: ladmin
'''

import os, stat, shutil, re
import json
from fabric import  colors, api as fab

from git import Repo
from git import Git
#from _ast import Try

class DockerfileFactory(object):
    
    def __init__(self):
        pass
        
    def reset(self, layer):
        self._dockerfile=Dockerfile(layerPath=layer)
    
    def get_mysqlDockerfile(self, layer):
        self.reset(layer)
        
    
    def get_Postgres96Dockerfile(self, layer):
        self.reset(layer)
        self._dockerfile.add_STRING('FROM postgres:9.6')
        self._dockerfile.add_STRING('MAINTAINER Aleksandr Gerasimov')
        self._dockerfile.COPY('docker-entrypoint-initdb.d/init-user-db.sh', '/docker-entrypoint-initdb.d/')
        self._dockerfile.COPY('tmp/', '/tmp/')
        self._dockerfile.COPY('patch.noerror.diff', '/tmp/patch.noerror.diff')
        self._dockerfile.add_STRING('RUN apt -y update && apt -y install vim patch')
        self._dockerfile.add_STRING('RUN ls ./ && pwd && patch /usr/local/bin/docker-entrypoint.sh < /tmp/patch.noerror.diff')
        return self._dockerfile
   
    def get_php73_fpmDictFile(self, layer):
        self.reset(layer)
        self._dockerfile.add_STRING('FROM php:7.4-fpm')
        self._dockerfile.add_STRING('RUN apt-get update && apt-get install -y curl wget git libfreetype6-dev libjpeg62-turbo-dev libxslt-dev libicu-dev libmcrypt-dev libpng-dev libxml2-dev libonig-dev libzip-dev')
        self._dockerfile.add_STRING('RUN docker-php-ext-install xml')
        self._dockerfile.add_STRING('RUN docker-php-ext-install -j$(nproc) iconv mbstring mysqli pdo_mysql zip')
        self._dockerfile.add_STRING('RUN docker-php-ext-configure gd --with-freetype=/usr/include/ --with-jpeg=/usr/include/')
        self._dockerfile.add_STRING('RUN docker-php-ext-install -j$(nproc) gd')
        self._dockerfile.add_STRING('RUN docker-php-ext-install opcache')
        self._dockerfile.add_STRING('RUN docker-php-ext-install bcmath')
        self._dockerfile.add_STRING('RUN docker-php-ext-install pdo')
        self._dockerfile.add_STRING('RUN docker-php-ext-configure intl')
        self._dockerfile.add_STRING('RUN docker-php-ext-install intl')
        self._dockerfile.add_STRING('RUN docker-php-ext-install xsl')
        self._dockerfile.add_STRING('RUN docker-php-ext-install soap')
        self._dockerfile.add_STRING('RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer')
        self._dockerfile.ADD('php.ini.custom', '$PHP_INI_DIR/conf.d/40-custom.ini')
        self._dockerfile.add_STRING('WORKDIR /usr/share/nginx/html')
        self._dockerfile.add_STRING('COPY html/ /usr/share/nginx/html/')
        self._dockerfile.add_STRING('EXPOSE 9000')
        self._dockerfile.add_STRING('CMD ["php-fpm"]')
        return self._dockerfile
    
  
    def get_nginxCommonDictFile(self, layer):
        self.reset(layer)
        self._dockerfile.add_STRING("FROM centos")
        self._dockerfile.add_STRING('RUN yum install epel-release -y')
        self._dockerfile.add_STRING('RUN yum install nginx -y')
        self._dockerfile.ADD('nginx.conf', '/etc/nginx/nginx.conf')
        self._dockerfile.ADD('public.html', '/usr/share/nginx/html/public.html')
        self._dockerfile.ADD('info.php', '/usr/share/nginx/html/info.php')
        self._dockerfile.add_STRING('EXPOSE 81')
        self._dockerfile.add_STRING('VOLUME [/share]')
        self._dockerfile.add_STRING('CMD ["nginx", "-g", "daemon off;"]')
        return self._dockerfile
    
    def get_nginxCommonDockerfile(self, layer):
        self.reset(layer)
        self._dockerfile.FROM("centos")
        self._dockerfile.RUN('yum install epel-release -y')
        self._dockerfile.RUN('yum install nginx -y')
        self._dockerfile.ADD('nginx.conf /etc/nginx/nginx.conf')
        self._dockerfile.ADD('public.html /usr/share/nginx/html/public.html')
        self._dockerfile.ADD('info.php /usr/share/nginx/html/info.php')
        self._dockerfile.EXPOSE('81')
        self._dockerfile.VOLUME('[/share]')
        self._dockerfile.CMD('["nginx", "-g", "daemon off;"]')
        self._dockerfile._file.close()
        return self._dockerfile    
        
    def get_php73_fpmDockerfile(self):
        self.reset()
        self._dockerfile.FROM('php:7.3-fpm')
        self._dockerfile.RUN('apt-get update && apt-get install -y curl wget git libfreetype6-dev libjpeg62-turbo-dev libxslt-dev libicu-dev libmcrypt-dev libpng-dev libxml2-dev libonig-dev libzip-dev')
        self._dockerfile.RUN('docker-php-ext-install -j$(nproc) iconv mbstring mysqli pdo_mysql zip')
        self._dockerfile.RUN('docker-php-ext-configure gd --with-freetype-dir=/usr/include/ --with-jpeg-dir=/usr/include/')
        self._dockerfile.RUN('docker-php-ext-install -j$(nproc) gd')
        self._dockerfile.RUN('docker-php-ext-configure intl')
        self._dockerfile.RUN('docker-php-ext-install intl')
        self._dockerfile.RUN('docker-php-ext-install xsl')
        self._dockerfile.RUN('docker-php-ext-install soap')
        self._dockerfile.RUN('curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer')
        self._dockerfile.ADD('php.ini.custom $PHP_INI_DIR/conf.d/40-custom.ini')
        self._dockerfile.WORKDIR('/usr/share/nginx/html')
        self._dockerfile.COPY('html/ /usr/share/nginx/html/')
        self._dockerfile.EXPOSE('9000')
        self._dockerfile.CMD('["php-fpm"]')
        self._dockerfile._file.close()
        return self._dockerfile

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
        self._index=0
        
    
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
        for key in self.dockerfile.keys():
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
    
    def add_STRING(self, str_content):   
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
        print(os.getcwd())
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
            
        print(os.path.join(self.layerPath, source))
        os.makedirs(os.path.dirname(os.path.join(self.layerPath, source)), stat.S_IRWXU, exist_ok=True)
        self.copyall(source, os.path.join(self.layerPath, source))
        self._increment()


class gitworker(object):
    '''
    Класс, реализующий доступ к репозиторию проекта
    '''
    gitrep=0

    def __init__(self, git_rep, wrapper):
        '''
        Constructor
        '''
        'ladmin@127.0.0.1:/git/itcluster/.git'
        self.gitrep=git_rep
        self.wrapper=wrapper
        #self.workdir='/home/ladmin/workspace_cpp/fabrica'   
    
    def prepare(self, workdir, cur_branch='master'):
        
        try:
            cur_repo = Repo(os.path.join(workdir, 'html'))
            assert not cur_repo.bare
             
        except:
            ssh_executable = os.path.join(self.workdir, self.wrapper)
            with  Git().custom_environment(GIT_SSH=ssh_executable):
                cur_repo = Repo.clone_from(self.gitrep, os.path.join(workdir, 'html'), branch=cur_branch)
        
        return cur_repo
    
    


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