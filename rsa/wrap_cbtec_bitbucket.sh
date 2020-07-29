#!/bin/sh
ID_RSA=/home/ladmin/.ssh/bitbacket_id_rsa
exec /usr/bin/ssh -o StrictHostKeyChecking=no -i $ID_RSA "$@"
