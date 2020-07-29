'''
Created on 30 июл. 2020 г.

@author: ladmin
'''

from srv.objectlib import Dockerfile

class DockerfileFactory(object):
    
    def __init__(self):
        pass
        
    def reset(self, layer):
        self._dockerfile=Dockerfile(layerPath=layer)
        
    def get_PostgresProvision(self, layer, imagever='20.04', dbname='dbname', dbuser='user', dbpass='pass'):
        self.reset(layer)
        self._dockerfile.add_STRING('FROM postgres:latest')
        self._dockerfile.add_STRING('ENV PGDATA /var/lib/postgresql-static/data')
        self._dockerfile.add_STRING('MAINTAINER Aleksandr Gerasimov')
        self._dockerfile.add_STRING('RUN apt update && apt install -y procps')
        self._dockerfile.COPY('postgresql.conf', '/postgresql.conf')
        self._dockerfile.add_STRING('RUN mkdir -p $PGDATA &&\
        chown -R postgres:postgres $PGDATA &&\
        chmod -R 700 $PGDATA')
        self._dockerfile.COPY('provision.sh', '/provision.sh')
        self._dockerfile.COPY('tmp/mk.sql', '/tmp/mk.sql')
        self._dockerfile.add_STRING('RUN chmod +x /provision.sh')
        self._dockerfile.add_STRING('RUN bash /provision.sh moscluster moscluster Li2iR0wLa5 /tmp/mk.sql')
        
        #self._dockerfile.add_STRING('RUN psql --command "CREATE USER '+dbuser+' WITH SUPERUSER PASSWORD \''+dbpass+'\;" && createdb -O '+dbname)
        #self._dockerfile.add_STRING('RUN echo "host all  all    0.0.0.0/0  md5" >> $PGDATA/pg_hba.conf')
        #self._dockerfile.add_STRING('RUN echo "listen_addresses='*'" >> $PGDATA/postgresql.conf')
        #self._dockerfile.add_STRING('USER postgres')
        #self._dockerfile.add_STRING('RUN gosu postgres initdb $PGDATA')
        
        #self._dockerfile.add_STRING('USER root')
        
        #self._dockerfile.add_STRING('USER postgres')
        #self._dockerfile.add_STRING('RUN ls -la /var/lib/postgresql/data/postgresql.conf')
        #self._dockerfile.add_STRING('RUN find / -name pg_*')
        #self._dockerfile.add_STRING('RUN gosu postgres postgres')
        #self._dockerfile.add_STRING('RUN psql --username '+dbuser+' --dbname '+dbname+' <<-EOSQL \
        #CREATE USER '+dbuser+'; \
        #CREATE DATABASE '+dbname+'; \
        #GRANT ALL PRIVILEGES ON DATABASE '+dbname+' TO '+dbuser+'; \
        #ALTER USER $CLUSTER_USER with PASSWORD \''+dbpass+'\';')
        #self._dockerfile.add_STRING('RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ focal-pgdg main" > /etc/apt/sources.list.d/pgdg.list')
        #self._dockerfile.add_STRING('RUN apt -y update && apt-get install -y python-software-properties software-properties-common postgresql-12')
        #self._dockerfile.add_STRING('VOLUME /var/lib/postgresql/data')
        self._dockerfile.add_STRING('ENTRYPOINT gosu postgres postgres -D $PGDATA')
        return self._dockerfile
     
    def get_PostgresProvision_old(self, layer, imagever='20.04', dbname='dbname', dbuser='user', dbpass='pass'):
        self.reset(layer)
        self._dockerfile.add_STRING('FROM ubuntu:latest')
        self._dockerfile.add_STRING('MAINTAINER Aleksandr Gerasimov')
        self._dockerfile.add_STRING('RUN apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys B97B0AFCAA1A47F044F244A07FCC7D46ACCC4CF8')
        self._dockerfile.add_STRING('RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ focal-pgdg main" > /etc/apt/sources.list.d/pgdg.list')
        self._dockerfile.add_STRING('RUN apt -y update && apt-get install -y python-software-properties software-properties-common postgresql-12')
        self._dockerfile.add_STRING('USER postgres')
        self._dockerfile.add_STRING('RUN /etc/init.d/postgresql start && psql --command "CREATE USER '+dbuser+' WITH SUPERUSER PASSWORD \''+dbpass+'\;" && createdb -O '+dbname)
        self._dockerfile.add_STRING('RUN echo "host all  all    0.0.0.0/0  md5" >> $PGDATA/pg_hba.conf')
        self._dockerfile.add_STRING('RUN echo "listen_addresses='*'" >> $PGDATA/postgresql.conf')
        self._dockerfile.add_STRING('USER postgres')
        self._dockerfile.add_STRING('USER postgres')
        self._dockerfile.add_STRING('VOLUME /var/lib/postgresql/data')
        return self._dockerfile
    
    def get_Postgres96Dockerfile(self, layer):
        self.reset(layer)
        self._dockerfile.add_STRING('FROM postgres:latest')
        self._dockerfile.add_STRING('MAINTAINER Aleksandr Gerasimov')
        self._dockerfile.COPY('docker-entrypoint-initdb.d/init-user-db.sh', '/docker-entrypoint-initdb.d/')
        self._dockerfile.COPY('tmp/', '/tmp/')
        self._dockerfile.COPY('patch.noerror.diff', '/tmp/patch.noerror.diff')
        self._dockerfile.add_STRING('RUN apt -y update && apt -y install vim patch')
        self._dockerfile.add_STRING('RUN env && pwd && patch /usr/local/bin/docker-entrypoint.sh < /tmp/patch.noerror.diff')
        self._dockerfile.add_STRING('RUN /docker-entrypoint.sh postgres')
        self._dockerfile.add_STRING('VOLUME /var/lib/postgresql/data')
        return self._dockerfile
   
    def get_php73_fpmDictFile(self, layer):
        self.reset(layer)
        self._dockerfile.add_STRING('FROM php:7.4-fpm', 10)
        self._dockerfile.add_STRING('RUN apt-get update && apt-get install -y gnupg2 sudo git curl wget net-tools', 20)
        self._dockerfile.add_STRING('RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -', 30)
        self._dockerfile.add_STRING('RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list', 40)
        self._dockerfile.add_STRING('RUN apt-get update && apt-get install -y yarn libgmp-dev libpq-dev curl wget git libfreetype6-dev libjpeg62-turbo-dev libxslt-dev libicu-dev libmcrypt-dev libpng-dev libxml2-dev libonig-dev libzip-dev', 50)
        self._dockerfile.add_STRING('RUN docker-php-ext-install xml', 60)
        self._dockerfile.add_STRING('RUN docker-php-ext-install -j$(nproc) iconv mbstring mysqli pdo_mysql zip', 70)
        self._dockerfile.add_STRING('RUN docker-php-ext-configure gd --with-freetype=/usr/include/ --with-jpeg=/usr/include/', 80)
        self._dockerfile.add_STRING('RUN docker-php-ext-install -j$(nproc) gd', 90)
        self._dockerfile.add_STRING('RUN docker-php-ext-install opcache', 100)
        self._dockerfile.add_STRING('RUN docker-php-ext-install bcmath', 110)
        self._dockerfile.add_STRING('RUN docker-php-ext-install pdo pdo_pgsql pgsql', 120)
        self._dockerfile.add_STRING('RUN docker-php-ext-configure intl', 130)
        self._dockerfile.add_STRING('RUN docker-php-ext-install intl', 140)
        self._dockerfile.add_STRING('RUN docker-php-ext-install xsl', 150)
        self._dockerfile.add_STRING('RUN docker-php-ext-install soap gmp', 160)
        self._dockerfile.add_STRING('RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer', 170)
        self._dockerfile.ADD('php.ini.custom', '$PHP_INI_DIR/conf.d/40-custom.ini', 180)
        self._dockerfile.add_STRING('WORKDIR /usr/share/nginx/html', 190)
        self._dockerfile.add_STRING('COPY html/ /usr/share/nginx/html/', 200)
        self._dockerfile.COPY('www.conf', '/usr/local/etc/php-fpm.d/docker.conf', 210)
        self._dockerfile.add_STRING('RUN ifconfig && route -n && mkdir -p /var/log/php-fpm  && touch /var/log/php-fpm/www.error.log && chown -R www-data:www-data /var/log/php-fpm', 220)
        #self._dockerfile.add_STRING('USER www-data', 230)
        self._dockerfile.add_STRING('RUN composer clearcache && composer install', 240)
        self._dockerfile.add_STRING('RUN php ./bin/console cache:clear', 250)
        self._dockerfile.add_STRING('RUN yarn install --silent', 260)
        self._dockerfile.COPY('fpmfiles/bootstrap.sh', '/usr/local/bin/bootstrap.sh', 270)
        self._dockerfile.add_STRING('RUN php bin/console assets:install --symlink', 280)
        self._dockerfile.add_STRING('RUN php bin/console sonata:page:update-core-routes --site=4', 290)
        self._dockerfile.add_STRING('RUN php bin/console sonata:page:create-snapshots --site=4', 300)
        self._dockerfile.add_STRING('RUN php bin/console fos:js-routing:dump --format=json --target=public/js/fos_js_routes.json', 310)
        #self._dockerfile.add_STRING('RUN php bin/console doctrine:migrations:migrate', 320)
        self._dockerfile.add_STRING('RUN yarn encore dev --silent', 330)
        self._dockerfile.add_STRING('RUN chown www-data:www-data -R /usr/share/nginx/html', 340)
        self._dockerfile.add_STRING('RUN chown www-data:www-data -R /var/www', 350)
        self._dockerfile.add_STRING('EXPOSE 9000', 360)
        self._dockerfile.add_STRING('VOLUME /usr/share/nginx/html', 370)
        self._dockerfile.add_STRING('CMD ["php-fpm"]', 380)
        return self._dockerfile
    
  
    def get_nginxCommonDictFile(self, layer):
        self.reset(layer)
        self._dockerfile.add_STRING("FROM centos")
        self._dockerfile.add_STRING('RUN yum install epel-release -y')
        self._dockerfile.add_STRING('RUN yum install nginx -y')
        #self._dockerfile.add_STRING('RUN curl --silent --location https://dl.yarnpkg.com/rpm/yarn.repo | tee /etc/yum.repos.d/yarn.repo')
        #self._dockerfile.add_STRING('RUN rpm --import https://dl.yarnpkg.com/rpm/pubkey.gpg')
        #self._dockerfile.add_STRING('RUN yum install yarn -y')
        #self._dockerfile.add_STRING('COPY html/ /usr/share/nginx/html/')
        self._dockerfile.ADD('itcluster.srvdev.ru.conf', '/etc/nginx/conf.d/itcluster.srvdev.ru.conf')
        self._dockerfile.ADD('.htpasswd', '/usr/share/nginx/.htpasswd')
        self._dockerfile.ADD('info.php', '/usr/share/nginx/html/info.php')
        self._dockerfile.add_STRING('WORKDIR /usr/share/nginx/html')
        #self._dockerfile.add_STRING('RUN yarn install')
        #self._dockerfile.add_STRING('RUN yarn encore dev')
        self._dockerfile.add_STRING('EXPOSE 80')
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