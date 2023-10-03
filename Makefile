install_deps:
	pip install -r requirements.txt ;\
	pip install pyinstaller

build:
	pyinstaller send_ardis.py -F