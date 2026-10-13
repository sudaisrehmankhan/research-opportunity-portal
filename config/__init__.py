import os


if os.getenv('DJANGO_DB_ENGINE') == 'django.db.backends.mysql':
    import pymysql

    pymysql.install_as_MySQLdb()