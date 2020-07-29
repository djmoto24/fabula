#!/bin/sh
ID_RSA=/home/ladmin/.ssh/id_rsa
exec /usr/bin/ssh -o StrictHostKeyChecking=no -i $ID_RSA "$@"
