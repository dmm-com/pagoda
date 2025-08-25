#!/bin/sh

# clear the database
for dir in `find ./ -name "migrations" -maxdepth 2`
do
  rm ${dir}/0*.py || true
done

# recreate database of MySQL
db_host=$(uv run python -c "from airone import settings; print(settings.DATABASES['default']['HOST'])")
db_name=$(uv run python -c "from airone import settings; print(settings.DATABASES['default']['NAME'])")
db_user=$(uv run python -c "from airone import settings; print(settings.DATABASES['default']['USER'])")
db_pass=$(uv run python -c "from airone import settings; print(settings.DATABASES['default']['PASSWORD'])")

echo "drop database ${db_name}" | mysql -u${db_user} -p${db_pass} -h${db_host}
echo "create database ${db_name}" | mysql -u${db_user} -p${db_pass} -h${db_host}

# re-construct database
uv run python manage.py makemigrations
uv run python manage.py migrate

# create an user of auto complementer
user_auto_complementer=$(uv run python -c "from airone import settings; print(settings.AIRONE['AUTO_COMPLEMENT_USER'])")
cat <<EOS | uv run python manage.py shell
from user.models import User
User.objects.create(username="${user_auto_complementer}")
EOS
