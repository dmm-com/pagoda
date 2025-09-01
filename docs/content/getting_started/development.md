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

And it's necessary to install `uv` command that manages Python packages and isolates Pagoda related libraries from system use ones.
```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then, you can install libraries on which Pagoda depends by following after cloning this repository. But we recommand you to setup pagoda on the separated environment using virtualenv not to pollute system-wide python environment.
```
user@hostname:~$ git clone https://github.com/dmm-com/pagoda.git
user@hostname:~$ cd pagoda
user@hostname:~/pagoda$ uv sync
```

Now, you have made Python environment for running Pagoda on your node. It'll be completed to run Pagoda when you install backend middlewares(MySQL, RabbitMQ and Elasticsearch).

There are two options to set them up.

## (Option1: Recommended) Setting-up backends using docker-compose

Check `docker` command has already been installed by following command.
```
$ sudo docker run hello-world
```

When `docker` command has not been installed, you should install Docker engine (c.f. [Install Docker Engine -- dockerdocs](https://docs.docker.com/engine/install/))

It's necessary to be able to run docker command without `sudo` because some script expect to run it by non-priviledged level.
```
### create docker group if it's necessary (it's OK to run this command when group 'docker' already exists)
$ sudo groupadd docker

### belong current user to docker group
$ sudo gpasswd -a $USER docker
```

Then, you can make middleware nodes (MySQL, RabbitMQ and Elasticsearch) by `docker compose` command as below.
```
user@hostname:~/pagoda$ sudo docker compose up -d
```

Then, you should make user for Pagoda (internally it was named as airone) to the Elasticsearch and MySQL as below.

### for Elasticsearch

You have to create user for Pagoda and set it administrative role at the Elasticsearch by following commands.
```
user@hostname:~$ sudo docker exec -it elasticsearch bin/elasticsearch-users useradd airone -p password
user@hostname:~$ sudo docker exec -it elasticsearch bin/elasticsearch-users roles airone --add superuser
```

You can check whether specified user was created successfully and has proper role as below.
```
user@hostname:~$ sudo docker exec -it elasticsearch bin/elasticsearch-users list
airone         : superuser
```

### for MySQL

Login to the Docker node that MySQL is running by following code.
```
user@hostname:~$ sudo docker exec -it mysql mysql -uroot
```

Then, you should cerate database and user for Pagoda (internally called `airone`) in MySQL.
```
mysql> create database airone;
mysql> create database test_airone;
mysql> CREATE USER 'airone'@'%' IDENTIFIED BY 'password';
mysql> GRANT ALL ON airone.* to airone@'%';
mysql> GRANT ALL ON test_airone.* to airone@'%';
```

(Optional) Please set the index as necessary.
```
mysql> CREATE INDEX permission_codename_idx ON auth_permission (codename);
```

Conguratulations, you completed to setup Pagoda execution environment.

After initializing Pagoda, you can use it! Please move on to the [Initialize Pagoda configuratoin](#initialize-pagoda-configuratoin).

## (Option2) Setting-up backends in manual

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

You should cerate database and user for pagoda in MySQL.
```
user@hostname:~$ mysql -u root -h 127.0.0.1

mysql> create database airone;
mysql> create database test_airone;
mysql> CREATE USER 'airone'@'%' IDENTIFIED BY 'password';
mysql> GRANT ALL ON airone.* to airone@'%';
mysql> GRANT ALL ON test_airone.* to airone@'%';
```

(Optional) Please set the index as necessary.
```
mysql> CREATE INDEX permission_codename_idx ON auth_permission (codename);
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

And you should create user and attach role in Elasticsearch.
```
bin/elasticsearch-users useradd airone -p password
bin/elasticsearch-users roles airone --add superuser
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

This command makes database schema using the [django Migrations](https://docs.djangoproject.com/en/1.11/topics/migrations/), and makes default user account.
```
user@hostname:~$ cd pagoda
user@hostname:~/pagoda$ tools/clear_and_initdb.sh
```

Then, you should create an initial user to login to the Pagoda. This creates user `demo`.
```
user@hostname:~/pagoda$ tools/register_user.sh demo
Password:   ## input password of this user
Succeed in register user (demo)
```

This creates following user.

| Username | Password |
|:---------|:---------|
| demo     | demo     |

If you want to create an administrative user who can access all information regardless of ACL (Please refer the [User-Manual(TBD)](#)), you can do it with `-s, --superuser` option. This creates another user who takes privilege of this system.
```
user@hostname:~/pagoda$ tools/register_user.sh -s admin
Password:   ## input password of this user
Succeed in register user (admin)
```

Finally, this registers all entries which has been created in the database to the Elasticsearch.  
You can do it just by following command. The configurations about the database to read and Elasticsearch to register are referred from airone/settings.py.

```
user@hostname:~/pagoda$ uv run python tools/initialize_es_document.py
```

## Run Pagoda
You can start Pagoda as following and can browse from `http://hostname:8080/`  
(Please change the `hostname` to the appropriate one on which you installed Pagoda).
e.g. 

```
user@hostname:~$ cd pagoda
user@hostname:~/pagoda$ uv run python manage.py runserver 0:8080
```

Then, you can access to the Pagoda by `http://localhost:8080` from your browser.

## Run Celery

In addition, you have to run Celery worker to execute background task (e.g. updating item).
Please open another terminal (or screen), then run it by following command.
```
user@hostname:~$ cd pagoda
user@hostname:~/pagoda$ uv run celery -A airone worker -l info
```

## Build the new UI with React

`/ui/` serves React-based new UI. Before you try it, you need to build `ui.js`:

### Preparing build environemnt

Prepare to install API client npm package published on GitHub Packages.
`TOKEN` is a your GitHub PAT. Issue your PAT with checking [this doc](https://docs.github.com/ja/packages/working-with-a-github-packages-registry/working-with-the-npm-registry#github-packages-%E3%81%B8%E3%81%AE%E8%AA%8D%E8%A8%BC%E3%82%92%E8%A1%8C%E3%81%86). This requires only `read:packages` scope.
Then, you just perform `npm install` as usual.

```
user@hostname:~/pagoda$ export TOKEN="(FIXME: github personal access token)"
user@hostname:~/pagoda$ cat <<EOS > .npmrc
//npm.pkg.github.com/:_authToken=${TOKEN}
EOS
```

After [installing nvm command](https://github.com/nvm-sh/nvm?tab=readme-ov-file#installing-and-updating), please install npm packages as below.
```
user@hostname:~$ nvm install 20
user@hostname:~$ cd pagoda
user@hostname:~/pagoda$ npm install
```

### Building pagoda react components

If you have any change on API V2, you need to run this command before you build:
```
user@hostname:~/pagoda$ npm run generate:client
```

Build Pagoda react component by following command.
```
(One time building)
user@hostname:~/pagoda$ npm run build

(In development)
user@hostname:~/pagoda$ npm run watch
```

### API V2 client

You can refer your local API client code before publishing it to GitHub Packages with following command.

```shell
user@hostname:~/pagoda$ npm run generate:client   # generate the latest API client code on your local env
user@hostname:~/pagoda$ npm run link:client       # refer the latest code temporarily
```

If you modify something in API client code, you need to publish it with the package release GitHub Actions workflow. It will be triggered by labeling `release-apiv2-client` to the pull request by repository owners.

## For Custom-View Building Procedure

When you want to ues Pagoda's Custom-View, you should run following command to build react environment considering CustomView.
```
user@hostname:~/pagoda$ npm run generate:custom_client

user@hostname:~/pagoda$ cp -pi ./frontend/src/App.tsx ./frontend/src/customview/CustomApp.tsx
(edit CustomApp.tsx)
user@hostname:~/pagoda$ npm run build:custom
```

## Auto-format

```
user@hostname:~$ cd pagoda
user@hostname:~/pagoda$ ruff format .
user@hostname:~/pagoda$ ruff check --fix .

user@hostname:~/pagoda$ npm run fix
```

## Test for Django processing
You can run tests for processing that is run by Django and Celery, which means backend processing, as below.
```
user@hostname:~$ cd pagoda
user@hostname:~/pagoda$ python manage.py test
```

When you want to run a specific test (`ModelTest.test_is_belonged_to_parent_group` in the file of `role/tests/test_model.py`) , you can do it as below.
```
user@hostname:~/pagoda$ python manage.py test role.tests.test_model.ModelTest.test_is_belonged_to_parent_group
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

## Release pagoda-core package for custom views

We publish the `pagoda-core` package to GitHub npm Registry for custom views.
When you want to release a new version of the package, create a tag with the format `pagoda-core-x.y.z` (e.g. `pagoda-core-0.0.1`). The GitHub Actions workflow will automatically build and publish the package.

If you hope to try building the module:

```sh
$ npm run build:lib
```
