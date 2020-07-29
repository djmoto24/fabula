FROM centos
RUN yum install epel-release -y
RUN yum install nginx -y
ADD nginx.conf /etc/nginx/nginx.conf
ADD public.html /usr/share/nginx/html/public.html
ADD info.php /usr/share/nginx/html/info.php
EXPOSE 81
VOLUME [/share]
CMD ["nginx", "-g", "daemon off;"]
