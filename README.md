# PG archives

This application manages PostgreSQL mailing list archives.  However, the search
feature is implemented in pgweb.

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
cd django
./manage.py migrate
```

Some suggested modifications to be later incorporated more formally.

```sql
INSERT INTO listgroups (groupid, groupname, sortkey) VALUES (1, 'Developer lists', 1);
INSERT INTO lists (listid, listname, shortdesc, description, active, groupid, subscriber_access) VALUES (1, 'pgsql-hackers', 'pgsql-hackers', 'The PostgreSQL developers team lives here. Discussion of current development issues, problems and bugs, and proposed new features. If your question cannot be answered by people in the other lists, and it is likely that only a developer will know the answer, you may re-post your question in this list. You must try elsewhere first!', True, 1, True);
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
