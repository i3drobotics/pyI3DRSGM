@echo off
python setup.py clean
python setup.py bdist_wheel --plat-name=win-amd64 --offline-installer=true