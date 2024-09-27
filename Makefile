install_deps:
	pip install -r src/requirements.txt
	pip install -r src/requirements.build.txt
ifeq ($(OS),Windows_NT)
	pip install -r src/requirements.windows.txt
endif

build-exe:
	pyinstaller src/send_ardis.py -F