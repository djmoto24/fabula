#!/bin/bash
set -e

#echo "===================== $CLUSTER_USER $CLUSTER_DB $CLUSTER_PASSWORD $POSTGRES_USER ========================"

psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER $CLUSTER_USER;
    CREATE DATABASE $CLUSTER_USER;
    GRANT ALL PRIVILEGES ON DATABASE $CLUSTER_DB TO $CLUSTER_USER;
    ALTER USER $CLUSTER_USER with PASSWORD '$CLUSTER_PASSWORD';
EOSQL
echo -e "psql -U "$CLUSTER_USER" "$CLUSTER_DB" < /tmp/$CUR_DUMP"
pg_restore --username "$CLUSTER_USER" --dbname "$CLUSTER_DB" /tmp/$CUR_DUMP

echo "================ END OF ALL ========================"
