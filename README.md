# PG archives

This application manages PostgreSQL mailing list archives.

## The Application

This is a Django 4.2 application backed by PostgreSQL and running on Python 3.x.

## Getting Started

### Ubuntu instructions

First, prepare your development environment by installing python3, postgresql-server-dev-X.Y, formail and libtidy (use `--no-install-recommends` to avoid installing postfix):

```bash
sudo apt install python3 postgresql-server-dev-14 procmail libtidy5deb1 --no-install-recommends
```

Next, configure your local environment with virtualenv and install local dependencies.

```bash
python3 -m venv env
source env/bin/activate
pip install -r dev_requirements.txt
```

Create a database for the application:

```bash
createdb archives
psql -d archives --set DEV=true -c '\i loader/sql/schema.sql' -c 'COMMIT'
```

Create config for the loader scripts:

```bash
cp loader/archives.ini.sample loader/archives.ini
```

Load some emails from the actual PostgreSQL archives by downloading an mbox
file from <https://www.postgresql.org/message-id/pgsql-hackers/> and running the
following command. NOTE: it's totally fine if some of the emails will fail to
load.

```bash
loader/load_message.py --list pgsql-hackers --mbox /path/to/downloaded/mbox/file
```

Then go to the `django` directory, that's where the actual web application is.

```bash
cd django
```

Create a local settings file (feel free to edit it):

```bash
cp archives/example_settings_local.py archives/settings_local.py
```

Finally, you're ready to start the web application:

```bash
./run_dev.py
```

Then open <http://localhost:8001/list/pgsql-hackers> to view your local mailing
list archives.
