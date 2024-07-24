#variables
PYTHON = python3
PIP = pip3

#paths
MAIN_SCRIPT = main.py
UTIL_SCRIPT = codegen.py
REQUIREMENTS_FILE = requirements.txt

#targets
.PHONY: all run test lint clean install

all: run

run:
	@$(PYTHON) $(MAIN_SCRIPT)

install:
	@$(PIP) install -r $(REQUIREMENTS_FILE)

clean:
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -r {} +

#End of Makefile

