#!/bin/bash
set -ue

show_usage() {
  echo "usage: $0 [options] username"
  echo ""
  echo "Options:"
  echo " -h, --help               display this help message and exit"
  echo " -p, --password PASSWORD  set password of creating user"
  echo " -s, --superuser          give priviledge of this system to creating user"
}

parse_argv() {
  USERNAME=""
  PASSWORD=""
  IS_ADMIN="False"

  while (( "$#" )); do
    case "$1" in
      -h|--help)
        show_usage
        exit 0
        ;;
      -s|--superuser)
        IS_ADMIN="True"
        shift 1
        ;;
      -p|--password)
        PASSWORD=$2
        shift 2
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
        USERNAME=$1
        shift
        ;;
    esac
  done

  if [ -z "$USERNAME" ]; then
    show_usage
    exit 1
  fi
}

main() {
  parse_argv $*

  # set password
  if [ -z "${PASSWORD}" ]; then
    read -sp "Password: " PASSWORD
  fi

  # create user
  cat <<EOS | python3 manage.py shell 2> /dev/null
from user.models import User

user = User.objects.filter(username='${USERNAME}').first()
if not user:
  user = User.objects.create(username='${USERNAME}', is_superuser=${IS_ADMIN})
 
user.is_superuser = ${IS_ADMIN}
user.set_password('${PASSWORD}')
user.email = '${USERNAME}@example.com'
user.save()
EOS

  echo
  echo "Succeed in register user ($USERNAME)"
}

main $*
