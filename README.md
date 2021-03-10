[![CircleCI](https://circleci.com/gh/dmm-com/airone.svg?style=svg&circle-token=2e12c068b0ed1bab9d0c2d72529d5ee1da9b53b4)](https://circleci.com/gh/dmm-com/airone)

# AirOne
This is a yet another DCIM(Data Center Infrastructure Management).

# Feature
These are the features of this software.
- Flexible permission setting. You can set permissions for each attribute data.
- Structured data. You can make data schema flexibly and dynamically.

# Setup
Here is the documentation to setup the development environment of AirOne.

## Installation of AirOne
You have to install Python3.5+ to run AirOne like below (for the case of `ubuntu`).
```
user@hostname:~$ sudo apt-get install python3 python3-pip virtualenv
```

And you have to install RabbitMQ for executing heavy processing as background task using [Celery](http://docs.celeryproject.org/) and Memcached for caching backend.
```
user@hostname:~$ sudo apt-get install rabbitmq-server memcached mysql-server python-dev libmysqlclient-dev
```

Then, you can install libraries on which AieOne depends by following after cloning this repository. But we recommand you to setup airone on the separated environment using virtualenv not to pollute system-wide python environment.
```
user@hostname:~$ cd airone
user@hostname:~/airone$ virtualenv -p python3 virtualenv
user@hostname:~/airone$ source virtualenv/bin/activate
(virtualenv) user@hostname:~/airone$ sudo pip install -r requirements.txt
```

### Setting-up MySQL configuration

You should cerate database and user for airone in MySQL.
```
user@hostname:~/airone$ sudo mysql -uroot

mysql> create database airone;
mysql> CREATE USER 'airone'@'localhost' IDENTIFIED BY 'password';
mysql> GRANT ALL ON airone.* to airone@'localhost' IDENTIFIED BY 'password';
```

And specifying character set of database is necessary. Please add following setting in the `mysqld.cnf` at `mysqld` section.
```
[mysqld]
...
character-set-server = utf8mb4
```

Then, you should restart MySQL server to apply for this configuration.
```
user@hostname:~$ sudo service mysql restart
```

### Initialize AirOne configuratoin
This command makes database schema using the [django Migrations](https://docs.djangoproject.com/en/1.11/topics/migrations/), and makes default user account.
```
user@hostname:~$ cd airone
user@hostname:~/airone$ source virtualenv/bin/activate
(virtualenv) user@hostname:~/airone$ tools/clear_and_initdb.sh
```

Finally, you should create an initial user to login the system using `tools/register_user.sh`.
```
(virtualenv) user@hostname:~/airone$ tools/register_user.sh demo
Password:   ## input password of this user
Succeed in register user (demo)
```

This creates following user.

| Username | Password |
|:---------|:---------|
| demo     | demo     |

If you want to create an administrative user who can access all information regardless of ACL (Please refer the [User-Manual(TBD)](#)), you can do it with `-s, --superuser` option. This creates another user who takes privilege of this system.
```
(virtualenv) user@hostname:~/airone$ tools/register_user.sh -s admin
Password:   ## input password of this user
Succeed in register user (admin)
```

## Run AirOne
You can start AirOne as following and can browse from `http://hostname:8080/` (Please change the `hostname` to the appropriate one on which you installed AirOne).

```
user@hostname:~/$ cd airone
user@hostname:~/airone$ source virtualenv/bin/activate
(virtualenv) user@hostname:~/airone/$ python3 manage.py collectstatic
(virtualenv) user@hostname:~/airone/$ python3 manage.py runserver 0:8080
```

## Run Celery

In addition, you have to run Celery worker to execute background task as following.
```
user@hostname:~/$ cd airone
user@hostname:~/airone$ source virtualenv/bin/activate
(virtualenv) user@hostname:~/airone$ celery -A airone worker -l info
```

## Run ElasticSearch
You have to setup JRE for executing elasticsearch.
```
user@hostname:~$ sudo add-apt-repository ppa:linuxuprising/java
user@hostname:~$ sudo apt-get update
user@hostname:~$ sudo apt-get install -y oracle-java13-installer
```

The way to install elasticsearch is quite easy like that.
```
user@hostname:~$ wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-6.8.12.tar.gz
user@hostname:~$ tar -xvf elasticsearch-6.8.12.tar.gz
```

After installing it, you have to change configuration to accept connecting from AirOne nodes.
```diff
--- elasticsearch-6.8.12/config/elasticsearch.yml.old        2020-01-29 10:19:40.511687943 +0900
+++ elasticsearch-6.8.12/config/elasticsearch.yml            2020-01-29 10:41:23.103687943 +0900
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
user@hostname:~$ elasticsearch-6.8.12/bin/elasticsearch
```

## Run Nginx (Optional)
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

Write following configuration for AirOne on Nginx at `/etc/nginx/conf.d/airone.conf`.
```
upstream airone {
  server hostname:8080;
}

server {
  listen 443 ssl;

  ssl_certificate /etc/nginx/ssl/server.crt;
  ssl_certificate_key /etc/nginx/ssl/server.key;

  proxy_set_header    Host    $host;
  proxy_set_header    X-Real-IP    $remote_addr;
  proxy_set_header    X-Forwarded-Host       $host;
  proxy_set_header    X-Forwarded-Server    $host;
  proxy_set_header    X-Forwarded-For    $proxy_add_x_forwarded_for;

  location / {
    rewrite ^/(.*) /$1 break;

    proxy_pass    http://airone/;
  }

  location /static {
    # Please change this appropriate path on your environment
    alias /home/ubuntu/airone/static;
  }

  access_log /var/log/nginx/airone.ssl.access.log combined;
  error_log /var/log/nginx/airone.ssl.error.log;

  # set longer to wait background processing until 300s
  proxy_read_timeout 300;
}
```

This includes the configuration to proxy HTTP request to AirOne and cache static files. The static file path indicates the static directory which is in the top of AirOne local repository. If necessary, please fix this value depending on your environment.

## Tools
There are some heler scripts about AirOne in the `tools` directory.

### register_es_documnt.py
This regists all entries which has been created in the database to the Elasticsearch.

#### Usage
You can do it just by following command. The configurations about the database to read and Elasticsearch to register are referred from airone/settings.py.

```
user@hostname:~/airone/$ tools/register_es_document.py
```

# Run with docker-compose

```
$ docker-compose up
```

## Setup virtualenv

```
$ python -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

## Setup database

```
$ mysql -uroot -h127.0.0.1 -e "GRANT ALL ON *.* to airone@'%' IDENTIFIED BY 'password'"
```

```
$ mysql -uairone -h127.0.0.1 -ppassword -e 'create database airone'
```

```
$ source venv/bin/activate
$ ./tools/clear_and_initdb.sh
```

```
$ source venv/bin/activate
$ ./tools/register_user.sh --superuser admin
Password:
Succeed in register user (admin)
```

## Run AirOne

```
$ source venv/bin/activate
$ python manage.py collectstatic
$ python manage.py runserver 0:8080
```

## Run Celery

```
$ source venv/bin/activate
$ celery -A airone worker -l info
```
