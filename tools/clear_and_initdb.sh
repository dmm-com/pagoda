#!/bin/bash
set -ue

show_usage() {
  echo "usage: $0 [options] username"
  echo ""
  echo "Options:"
  echo " -b, --beremetal          expect each middlewares are running on the baremetal environment"
}

parse_argv() {
  IS_BEREMETAL="false"

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
  if [ ${IS_BEREMETAL} = "true" ]
  then
    db_host=$(uv run python -c "from airone import settings; print(settings.DATABASES['default']['HOST'])")
    db_user=$(uv run python -c "from airone import settings; print(settings.DATABASES['default']['USER'])")
    db_pass=$(uv run python -c "from airone import settings; print(settings.DATABASES['default']['PASSWORD'])")

    MYSQL_COMMAND="mysql -u${db_user} -p${db_pass} -h${db_host}"
  else
    MYSQL_COMMAND="sudo docker exec -it mysql mysql -uroot"
  fi

  # recreate MySQL databse
  ${MYSQL_COMMAND} -e "drop database ${db_name}"
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
