#!/bin/sh

# clear the database
for dir in `find ./ -name "migrations"`
do
  rm ${dir}/0*.py || true
done

# recreate database of MySQL
db_host=$(python3 -c "from airone import settings; print(settings.DATABASES['default']['HOST'])")
db_name=$(python3 -c "from airone import settings; print(settings.DATABASES['default']['NAME'])")
db_user=$(python3 -c "from airone import settings; print(settings.DATABASES['default']['USER'])")
db_pass=$(python3 -c "from airone import settings; print(settings.DATABASES['default']['PASSWORD'])")

echo "drop database ${db_name}" | mysql -u${db_user} -p${db_pass} -h${db_host}
echo "create database ${db_name}" | mysql -u${db_user} -p${db_pass} -h${db_host}

# re-construct database
python3 manage.py makemigrations
python3 manage.py migrate

# create an user of auto complementer
user_auto_complementer=$(python3 -c "from airone import settings; print(settings.AIRONE['AUTO_COMPLEMENT_USER'])")
cat <<EOS | python3 manage.py shell
from user.models import User
User.objects.create(username="${user_auto_complementer}")
EOS
