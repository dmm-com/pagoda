---
title: Development
weight: 30
---

# Setup
Here is the documentation to setup the development environment of Pagoda.

## Installation of Pagoda
You have to install Python3.11+ to run Pagoda like below (for the case of `ubuntu`).
```
user@hostname:~$ sudo apt-get update
user@hostname:~$ sudo apt-get install python3 python3-pip python3-venv
```

You have to install libraries.
```
user@hostname:~$ sudo apt-get install libldap2-dev  libsasl2-dev libxmlsec1-dev libmysqlclient-dev pkg-config
```

(for macOS)
```
user@hostname:~$ brew install libxmlsec1 mysql-client pkg-config mysql-connector-python
```

Then, you can install libraries on which Pagoda depends by following after cloning this repository. But we recommand you to setup pagoda on the separated environment using virtualenv not to pollute system-wide python environment.
```
user@hostname:~$ git clone https://github.com/dmm-com/pagoda.git
user@hostname:~$ cd pagoda
user@hostname:~/pagoda$ python3 -m venv virtualenv
user@hostname:~/pagoda$ source virtualenv/bin/activate
(virtualenv) user@hostname:~/pagoda$ pip install pip --upgrade
(virtualenv) user@hostname:~/pagoda$ pip install poetry
(virtualenv) user@hostname:~/pagoda$ poetry install --only main
# or, during development, install all
(virtualenv) user@hostname:~/pagoda$ poetry install
```

## Setting-up Backend with docker-compose

Install docker-compose command.  
Run middlewares with docker-compose.

```
user@hostname:~/pagoda$ docker-compose up
```

## (Setting-up Backend with manual)

And you have to install RabbitMQ for executing heavy processing as background task using [Celery](http://docs.celeryproject.org/).
```
user@hostname:~$ sudo apt-get install rabbitmq-server mysql-server python-dev libmysqlclient-dev
```

### Setting-up MySQL configuration

Specifying character set of database is necessary. Please add following setting in the `mysqld.cnf` at `mysqld` section.
```
[mysqld]
...
character-set-server = utf8mb4
```

Then, you should restart MySQL server to apply for this configuration.
```
user@hostname:~$ sudo service mysql restart
```

Iincrease the number of Slave databases with the MySQL replication function.  
You can set database slave, with like this config:
```
REPLICATED_DATABASE_SLAVES = ['slave1', 'slave2']
```

### Setting-up Elasticsearch

You have to setup JRE for executing elasticsearch.
```
user@hostname:~$ sudo add-apt-repository ppa:linuxuprising/java
user@hostname:~$ sudo apt-get update
user@hostname:~$ sudo apt-get install -y oracle-java13-installer
```

The way to install elasticsearch is quite easy like that.
```
user@hostname:~$ wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-7.17.6-linux-x86_64.tar.gz
user@hostname:~$ tar -xvf elasticsearch-7.17.6-linux-x86_64.tar.gz
```

After installing it, you have to change configuration to accept connecting from Pagoda nodes.
```diff
--- elasticsearch-7.17.6-linux-x86_64/config/elasticsearch.yml.old        2020-01-29 10:19:40.511687943 +0900
+++ elasticsearch-7.17.6-linux-x86_64/config/elasticsearch.yml            2020-01-29 10:41:23.103687943 +0900
@@ -52,7 +52,7 @@
 #
 # Set the bind address to a specific IP (IPv4 or IPv6):
 #
-#network.host: 192.168.0.1
+network.host: 0.0.0.0
 #
 # Set a custom port for HTTP:
 #
```

You should set sysctl as below because Elasticsearch requires to expand virtual memory area.
```
user@hostname:~$ sudo sysctl vm.max_map_count=262144
```

Finally, you can run ElasticSearch service like that.
```
user@hostname:~$ elasticsearch-7.17.6-linux-x86_64/bin/elasticsearch
```

### Setting-up Email configuration

This step is optional. You can skip it if you don't use email notifications.

Pagoda supports email based notification, now it's mainly used for password-reset. You can set email backend, with like this config:

```
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'xxx'
EMAIL_PORT = 25
EMAIL_HOST_USER = 'xxx'
EMAIL_HOST_PASSWORD = 'xxx'
EMAIL_USE_TLS = True
```

If you hope to just try it in your local environment, you can use stdout instead:

```
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

## Setting-up Nginx (Optional)
Install Nginx by package manager like this.
```
user@hostname:~$ sudo apt-get install nginx
```

Create Self-Signed SSL Certificate and key-pair.
```
user@hostname:~$ openssl genrsa 2048 > server.key
user@hostname:~$ openssl req -new -key server.key > server.csr
... (set appropriate configuration)

user@hostname:~$ openssl x509 -days 3650 -req -signkey server.key < server.csr > server.crt
user@hostname:~$ sudo mkdir /etc/nginx/ssl
user@hostname:~$ sudo mv server* /etc/nginx/ssl
```

Write following configuration for Pagoda on Nginx at `/etc/nginx/conf.d/pagoda.conf`.
```
upstream pagoda {
  server hostname:8080;
}

server {
  listen 443 ssl;

  ssl_certificate /etc/nginx/ssl/server.crt;
  ssl_certificate_key /etc/nginx/ssl/server.key;

  proxy_set_header    Host    $host;
  proxy_set_header    X-Real-IP    $remote_addr;
  proxy_set_header    X-Forwarded-Host    $host;
  proxy_set_header    X-Forwarded-Server    $host;
  proxy_set_header    X-Forwarded-For    $proxy_add_x_forwarded_for;
  proxy_set_header    X-Forwarded-Proto    $scheme;
  proxy_set_header    X-Forwarded-Port    443;

  location / {
    rewrite ^/(.*) /$1 break;

    proxy_pass    http://pagoda/;
  }

  access_log /var/log/nginx/pagoda.ssl.access.log combined;
  error_log /var/log/nginx/pagoda.ssl.error.log;

  # set longer to wait background processing until 300s
  proxy_read_timeout 300;
}
```

This includes the configuration to proxy HTTP request to Pagoda and cache static files. The static file path indicates the static directory which is in the top of Pagoda local repository. If necessary, please fix this value depending on your environment.

## Initialize Pagoda configuratoin

You should create user and attach role in Elasticsearch.
```
bin/elasticsearch-users useradd airone
bin/elasticsearch-users roles airone --add superuser
```

You should cerate database and user for pagoda in MySQL.
```
user@hostname:~$ mysql -u root -h 127.0.0.1

mysql> create database airone;
mysql> create database test_airone;
mysql> CREATE USER 'airone'@'%' IDENTIFIED BY 'password';
mysql> GRANT ALL ON airone.* to airone@'%';
mysql> GRANT ALL ON test_airone.* to airone@'%';
```

This command makes database schema using the [django Migrations](https://docs.djangoproject.com/en/1.11/topics/migrations/), and makes default user account.
```
user@hostname:~$ cd pagoda
user@hostname:~/pagoda$ source virtualenv/bin/activate
(virtualenv) user@hostname:~/pagoda$ tools/clear_and_initdb.sh
```

(Optional) Please set the index as necessary.
```
mysql> CREATE INDEX permission_codename_idx ON auth_permission (codename);
```

Finally, you should create an initial user to login the system using `tools/register_user.sh`.
```
(virtualenv) user@hostname:~/pagoda$ tools/register_user.sh demo
Password:   ## input password of this user
Succeed in register user (demo)
```

This creates following user.

| Username | Password |
|:---------|:---------|
| demo     | demo     |

If you want to create an administrative user who can access all information regardless of ACL (Please refer the [User-Manual(TBD)](#)), you can do it with `-s, --superuser` option. This creates another user who takes privilege of this system.
```
(virtualenv) user@hostname:~/pagoda$ tools/register_user.sh -s admin
Password:   ## input password of this user
Succeed in register user (admin)
```

This regists all entries which has been created in the database to the Elasticsearch.  
You can do it just by following command. The configurations about the database to read and Elasticsearch to register are referred from airone/settings.py.

```
(virtualenv) user@hostname:~/pagoda$ python tools/initialize_es_document.py
```

## Run Pagoda
You can start Pagoda as following and can browse from `http://hostname:8080/`  
(Please change the `hostname` to the appropriate one on which you installed Pagoda).
e.g. 

```
user@hostname:~$ cd pagoda
user@hostname:~/pagoda$ source virtualenv/bin/activate
(virtualenv) user@hostname:~/pagoda$ python manage.py runserver 0:8080
```

## Run Celery

In addition, you have to run Celery worker to execute background task as following.
```
user@hostname:~$ cd pagoda
user@hostname:~/pagoda$ source virtualenv/bin/activate
(virtualenv) user@hostname:~/pagoda$ celery -A airone worker -l info
```

## [Experimental] Build the new UI with React

`/ui/` serves React-based new UI. Before you try it, you need to build `ui.js`:

Install nvm command.  

Install npm packages.
```
user@hostname:~$ nvm install 18.12.0
user@hostname:~$ cd pagoda
user@hostname:~/pagoda$ npm install
```

Build
```
user@hostname:~/pagoda$ npm run build

(In development)
user@hostname:~/pagoda$ npm run watch
```

If you have any change on API V2, you need to run this command before you build:

```
user@hostname:~/pagoda$ npm run generate:client

(For Customview)
user@hostname:~/pagoda$ npm run generate:custom_client
```

To customize UI:

```
user@hostname:~/pagoda$ cp -pi ./frontend/src/App.tsx ./frontend/src/customview/CustomApp.tsx
(edit CustomApp.tsx)
user@hostname:~/pagoda$ npm run build:custom
```

### API V2 client

Prepare to install API client npm package published on GitHub Packages.
`TOKEN` is a your GitHub PAT. Issue your PAT with checking [this doc](https://docs.github.com/ja/packages/working-with-a-github-packages-registry/working-with-the-npm-registry#github-packages-%E3%81%B8%E3%81%AE%E8%AA%8D%E8%A8%BC%E3%82%92%E8%A1%8C%E3%81%86).
Then, you just perform `npm install` as usual.

```
$ cat > .npmrc
//npm.pkg.github.com/:_authToken=TOKEN
```

You can refer your local API client code before publishing it to GitHub Packages with following command.

```shell
# generate the latest API client code on your local env
$ npm run generate:client

# refer the latest code temporarily
$ npm run link:client
```

If you modify something in API client code, you need to publish it with the package release GitHub Actions workflow. It will be triggered by labeling `release-apiv2-client` to the pull request by repository owners.

## Auto-format

```
user@hostname:~$ cd pagoda
user@hostname:~/pagoda$ source virtualenv/bin/activate
(virtualenv) user@hostname:~/pagoda$ ruff format .
(virtualenv) user@hostname:~/pagoda$ ruff check --fix .

user@hostname:~/pagoda$ npm run fix
```

## Test for Django processing
You can run tests for processing that is run by Django and Celery, which means backend processing, as below.
```
user@hostname:~$ cd pagoda
user@hostname:~/pagoda$ source virtualenv/bin/activate
(virtualenv) user@hostname:~/pagoda$ python manage.py test
```

When you want to run a specific test (`ModelTest.test_is_belonged_to_parent_group` in the file of `role/tests/test_model.py`) , you can do it as below.
```
(virtualenv) user@hostname:~/pagoda$ python manage.py test role.tests.test_model.ModelTest.test_is_belonged_to_parent_group
```

## Test for React processing
You can run test for processing that is run by Browser, wihch means frontend processing as below.
```
user@hostname:~$ cd pagoda
user@hostname:~/pagoda$ npm run test
```

If you have any change on a page component, please re-build snapshots along with current implementaion as below.

```
user@hostname:~/pagoda$ npm run test:update
```

When you want to run individual test (e.g. frontend/src/components/user/UserList.test.tsx), you can do it by following command.
```
user@hostname:~/pagoda$ npx jest -u frontend/src/components/user/UserList.test.tsx
```
