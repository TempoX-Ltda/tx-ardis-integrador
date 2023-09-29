install_deps:
	pip install -r requirements.txt ;\
	pip install pyinstaller

build:
	pyinstaller busca_retrabalho.py -F