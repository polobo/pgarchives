# A handy target to reset the development environment back to a clean slate
# and run the development server.
# XXX: For now just use the single mbox file that was previously downloaded.
#      Additional work in this area, for testing use cases, is needed.
dev-rebuild-and-run:
	dropdb --if-exists archives
	createdb archives
	django/manage.py migrate
	loader/load_message.py --list pgsql-hackers --mbox mboxes/pgsql-hackers.202504 >/dev/null
	cd ./django && ./run_dev.py
