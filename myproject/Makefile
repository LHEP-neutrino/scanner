VENV=/opt/myproject/venv
PYTHON=$(VENV)/bin/python
PIP=$(VENV)/bin/pip
ADMIN=$(VENV)/bin/myproject-admin

.PHONY: install uninstall reinstall logs status

install:
	python3 -m venv $(VENV)
	$(PIP) install .
	sudo $(ADMIN) install

uninstall:
	sudo $(ADMIN) uninstall
	sudo rm -rf $(VENV)

	