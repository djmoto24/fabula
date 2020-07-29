FROM php:7.4-fpm
RUN apt-get update && apt-get install -y curl wget git libfreetype6-dev libjpeg62-turbo-dev libxslt-dev libicu-dev libmcrypt-dev libpng-dev libxml2-dev libonig-dev libzip-dev
RUN docker-php-ext-install xml
RUN docker-php-ext-install -j$(nproc) iconv mbstring mysqli pdo_mysql zip
RUN docker-php-ext-configure gd --with-freetype=/usr/include/ --with-jpeg=/usr/include/
RUN docker-php-ext-install -j$(nproc) gd
RUN docker-php-ext-install opcache
RUN docker-php-ext-install bcmath
RUN docker-php-ext-install pdo
RUN docker-php-ext-configure intl
RUN docker-php-ext-install intl
RUN docker-php-ext-install xsl
RUN docker-php-ext-install soap
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer
ADD php.ini.custom $PHP_INI_DIR/conf.d/40-custom.ini
WORKDIR /usr/share/nginx/html
COPY html/ /usr/share/nginx/html/
EXPOSE 9000
CMD ["php-fpm"]
