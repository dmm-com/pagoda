# AirOne
This is a yet another DCIM(Data Center Infrastructure Management).

# Feature
These are the features of this software.
- Flexible permission setting. You can set permissions for each attribute data.
- Structured data. You can make data schema flexibly and dynamically.

# Setup
Here is the documentation to setup the development environment of AirOne.

## Preparation
You have to install Python3.5+ to run AirOne like below (for the case of `ubuntu`).
```
$ sudo apt-get install python3 python3-pip
```

And you have to install RabbitMQ for executing heavy processing as background task using [Celery](http://docs.celeryproject.org/) and Memcached for caching backend.
```
$ sudo apt-get install rabbitmq-server memcached mysql-server python-dev libmysqlclient-dev
```

Then, you can install libraries on which AieOne depends by following after cloning this repository.
```
$ cd airone
$ sudo pip install -r requirements.txt
```

Cerate database and user for airone in MySQL.
```
$ mysql -uroot -p****

mysql> create database airone;
mysql> CREATE USER 'airone'@'localhost' IDENTIFIED BY 'password';
mysql> GRANT ALL ON airone.* to airone@'localhost' IDENTIFIED BY 'password';
```

This command makes database schema using the [django Migrations](https://docs.djangoproject.com/en/1.11/topics/migrations/), and makes default user account.
```
$ tools/clear_and_initdb.sh
```

This is the default account information.

| Username | Password |
|:---------|:---------|
| demo     | demo     |

Finally, you can start AirOne and can browse from `http://hostname:8080/`.
```
$ python3 manage.py runserver 0:8080
```

### Celery

In addition, you have to run Celery worker to execute background task as following.
```
$ celery -A airone worker -l info
```

### ElasticSearch
You have to setup Java8 for executing elasticsearch. Here is the procedure to setup `Oracle JDK 8`.
```
$ sudo add-apt-repository ppa:webupd8team/java
$ sudo apt-get update
$ sudo apt-get install oracle-java8-installer
```

The way to install elasticsearch is quite easy like that.
```
$ wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-6.2.3.tar.gz
$ tar -xvf elasticsearch-6.2.3.tar.gz
```

After installing it, you have to change configuration to accept connecting from AirOne nodes.
```diff
--- elasticsearch-6.2.3/config/elasticsearch.yml.old        2018-03-13 19:02:56.000000000 +0900
+++ elasticsearch-6.2.3/config/elasticsearch.yml            2018-05-10 16:35:25.872529462 +0900
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

Then, you can execute ElasticSearch search like that.
```
$ elasticsearch-6.2.3/bin/elasticsearch
```

### Nginx
Install Nginx by package manager like this.
```
$ sudo apt-get install nginx
```

Create Self-Signed SSL Certificate and key-pair.
```
$ openssl genrsa 2048 > server.key
$ openssl req -new -key server.key > server.csr
... (set appropriate configuration)

$ openssl x509 -days 3650 -req -signkey server.key < server.csr > server.crt
$ sudo mkdir /etc/nginx/ssl
$ sudo mv server* /etc/nginx/ssl
```

Write following configuration for AirOne on Nginx at `/etc/nginx/conf.d/airone.conf`.
```
upstream airone {
  server localhost:8080;
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
$ tools/register_es_document.py
```
