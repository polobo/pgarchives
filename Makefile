dev-rebuild-and-run:
	dropdb --if-exists archives
	createdb archives
	django/manage.py migrate
	loader/load_message.py --list pgsql-hackers --mbox ~/Downloads/pgsql-hackers.202504
	cd ./django && ./run_dev.py
