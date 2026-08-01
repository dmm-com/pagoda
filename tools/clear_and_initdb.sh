#!/bin/bash
set -ue

show_usage() {
  echo "usage: $0 [options] username"
  echo ""
  echo "Options:"
  echo " -b, --beremetal          expect each middlewares are running on the baremetal environment"
}

parse_argv() {
  IS_BAREMETAL="false"

  while (( "$#" )); do
    case "$1" in
      -h|--help)
        show_usage
        exit 0
        ;;
      -b|--baremetal)
        IS_BAREMETAL="true"
        shift 1
        ;;
      --) # end argument parsing
        shift
        break
        ;;
      -*|--*=)
        echo "Error: Unsupported flag ($1) is specified" >&2
        exit 1
        ;;
      *)
        ;;
    esac
  done
}

main() {
  parse_argv $*

  # clear the database
  for dir in `find ./ -name "migrations" -maxdepth 2`
  do
    rm ${dir}/0*.py || true
  done

  db_name=$(uv run python -c "from airone import settings; print(settings.DATABASES['default']['NAME'])")
  db_host=$(uv run python -c "from airone import settings; print(settings.DATABASES['default']['HOST'])")
  db_user=$(uv run python -c "from airone import settings; print(settings.DATABASES['default']['USER'])")
  db_pass=$(uv run python -c "from airone import settings; print(settings.DATABASES['default']['PASSWORD'])")

  # The root account of the local MySQL has no password by default. Set the
  # MYSQL_ROOT_PASSWORD environment variable when it is protected.
  root_pass_opt=""
  if [ -n "${MYSQL_ROOT_PASSWORD:-}" ]
  then
    root_pass_opt="-p${MYSQL_ROOT_PASSWORD}"
  fi

  if [ ${IS_BAREMETAL} = "true" ]
  then
    MYSQL_COMMAND="mysql -u${db_user} -p${db_pass} -h${db_host}"
    MYSQL_ROOT_COMMAND="mysql -uroot ${root_pass_opt} -h${db_host}"
  else
    MYSQL_COMMAND="sudo docker exec -i mysql mysql -uroot ${root_pass_opt}"
    MYSQL_ROOT_COMMAND="${MYSQL_COMMAND}"
  fi

  # create the database user that is configured in the settings, because the
  # following operations fail when it doesn't exist yet (e.g. a fresh MySQL
  # container that only has the root account)
  ${MYSQL_ROOT_COMMAND} <<EOS
CREATE USER IF NOT EXISTS '${db_user}'@'%' IDENTIFIED BY '${db_pass}';
ALTER USER '${db_user}'@'%' IDENTIFIED BY '${db_pass}';
GRANT ALL PRIVILEGES ON *.* TO '${db_user}'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;
EOS

  # recreate MySQL databse
  ${MYSQL_COMMAND} -e "drop database if exists ${db_name}"
  ${MYSQL_COMMAND} -e "create database ${db_name}"

  # re-construct database
  uv run python manage.py makemigrations
  uv run python manage.py migrate

  # create an user of auto complementer
  user_auto_complementer=$(uv run python -c "from airone import settings; print(settings.AIRONE['AUTO_COMPLEMENT_USER'])")
  cat <<EOS | uv run python manage.py shell
from user.models import User
User.objects.create(username="${user_auto_complementer}")
EOS
}

main $*
