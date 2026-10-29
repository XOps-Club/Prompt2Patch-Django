.PHONY: setup dev run stop test test-eval test\:eval migrate seed install clean

ifeq ($(OS),Windows_NT)
PYTHON = .venv/Scripts/python.exe
PIP = .venv/Scripts/pip.exe
PYTHON_BOOTSTRAP = python
else
PYTHON = .venv/bin/python
PIP = .venv/bin/pip
PYTHON_BOOTSTRAP = python3
endif

setup: install migrate seed

dev: run

run:
ifeq ($(OS),Windows_NT)
	$(PYTHON) manage.py runserver 127.0.0.1:8000
else
	@fuser -k -9 8000/tcp 2>/dev/null || true
	$(PYTHON) manage.py runserver 0.0.0.0:8000
endif

stop:
ifeq ($(OS),Windows_NT)
	@echo "Use Ctrl+C in the make run window to stop the server."
else
	@fuser -k -9 8000/tcp 2>/dev/null || true
endif

test:
	$(PYTHON) manage.py test links

test-eval:
	@if [ -f backend/links/eval_hidden.py ]; then \
		$(PYTHON) manage.py test links.eval_hidden; \
	else \
		echo "[Evaluation] Hidden evaluation suite (links.eval_hidden) is reserved for grading."; \
	fi

test\:eval: test-eval

migrate:
	$(PYTHON) manage.py migrate

makemigrations:
	$(PYTHON) manage.py makemigrations

seed:
	$(PYTHON) manage.py seed

install:
	$(PYTHON_BOOTSTRAP) -m venv .venv
	$(PIP) install -r requirements.txt

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
