#!/bin/bash
set -e
CLUSTER_DB=$1
CLUSTER_USER=$2
CLUSTER_PASSWORD=$3
CUR_DUMP=$4

docker_temp_server_start() {
        # internal start of server in order to allow setup using psql client
        # does not listen on external TCP/IP and waits until start finishes
        set -- "$@" -c listen_addresses='' -p "${PGPORT:-5432}"

	echo "$(printf '%q ' "$@")"
	sleep 10
        gosu postgres pg_ctl -D "$PGDATA" \
                -o "$(printf '%q ' "$@")" \
                -w start
}


docker_temp_server_stop() {
        gosu postgres pg_ctl -D "$PGDATA" -m smart -w stop
}

pg_setup_hba_conf() {
        local authMethod='md5'
        #if [ -z "$POSTGRES_PASSWORD" ]; then
        #        authMethod='trust'
        #fi

        {
                echo
                echo "host all all all $authMethod"
        } >> "$PGDATA/pg_hba.conf"
}



mkdir -p $PGDATA
chown -R postgres:postgres $PGDATA
chmod -R 700 $PGDATA
ls -la /var/log/postgresql/ && ls -la $PGDATA

gosu postgres pg_ctl -D $PGDATA initdb 

gosu postgres cp /postgresql.conf $PGDATA/postgresql.conf
ls -la $PGDATA/postgresql.conf

#gosu postgres postgres &
docker_temp_server_start

echo "===================== $CLUSTER_USER $CLUSTER_DB $CLUSTER_PASSWORD $POSTGRES_USER ========================"

gosu postgres psql <<-EOSQL
    CREATE USER $CLUSTER_USER;
    CREATE DATABASE $CLUSTER_USER;
    GRANT ALL PRIVILEGES ON DATABASE $CLUSTER_DB TO $CLUSTER_USER;
    ALTER USER $CLUSTER_USER with PASSWORD '$CLUSTER_PASSWORD';
EOSQL
echo -e "psql -U "$CLUSTER_USER" "$CLUSTER_DB" < /tmp/$CUR_DUMP"
gosu postgres pg_restore --username "$CLUSTER_USER" --dbname "$CLUSTER_DB" $CUR_DUMP &> $PGDATA/pgrestore.log

gosu postgres psql -U postgres --list
#gosu postgres psql <<-EOSQL
#    COMMIT;
#EOSQL

#sleep 15
docker_temp_server_stop
pg_setup_hba_conf
#docker_temp_server_start
#gosu postgres psql -U postgres --list
#docker_temp_server_stop

echo "================ END OF ALL ========================"

