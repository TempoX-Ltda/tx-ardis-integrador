install_deps:
	pip install -r src/requirements.txt ;\
	pip install pyinstaller

build:
	pyinstaller src/send_ardis.py -F