#!/bin/bash
provisionIfNeeded()
{
    PROVISIONED=/tmp/provisioned
    if [ ! -f ${PROVISIONED} ]; then

        echo "------------------------------------------------------------------------------"
        echo "Provisioning"
        echo "------------------------------------------------------------------------------"

	php bin/console cache:clear
	php bin/console assets:install --symlink
	#yarn install
	yarn encore dev
	php bin/console sonata:page:update-core-routes --site=4
	php bin/console sonata:page:create-snapshots --site=4
	php bin/console fos:js-routing:dump --format=json --target=public/js/fos_js_routes.json
	php bin/console doctrine:migrations:migrate
        #comiposer --no-ansi --no-interaction dump-autoload --no-dev --optimize --classmap-authoritative --no-scripts && \
        #composer --no-ansi --no-interaction run-script --no-dev symfony-scripts
        #php bin/console cache:clear && \
        #php bin/console cache:clear --env=prod && \
        #php bin/console assetic:dump --env=prod

        echo "------------------------------------------------------------------------------"
        echo "Ended provisioning"
        echo "------------------------------------------------------------------------------"

        touch ${PROVISIONED}
    fi
}

startServer()
{
    echo "Starting httpd."
    php-fpm
}

provisionIfNeeded
startServer
