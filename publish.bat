@echo off

:: read version from file
set /p version=< version.txt

rmdir /s /q release
mkdir release


python -m pip install --upgrade pip
python -m pip install setuptools wheel twine
python -m pip install flake8 pytest

cd i3drsgm
python -m pip install --upgrade -r requirements.txt --no-cache
pytest

if %ERRORLEVEL% GEQ 1 EXIT /B 1

python setup.py clean
python setup.py sdist bdist_wheel --plat-name=win-amd64 --offline-installer=false

twine upload --repository-url https://test.pypi.org/legacy/ dist/*
twine upload dist/*

cd ..
