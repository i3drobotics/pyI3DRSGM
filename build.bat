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
python setup.py bdist_wheel --plat-name=win-amd64 --offline-installer=true
cd ..
ren i3drsgm\dist\i3drsgm-%version%-py3-none-win_amd64.whl i3drsgm-%version%-py3-none-win_amd64-offline.whl
copy i3drsgm\dist\i3drsgm-%version%-py3-none-win_amd64-offline.whl release\

cd i3drsgm
python setup.py clean
python setup.py bdist_wheel --plat-name=win-amd64 --offline-installer=false
cd ..
echo i3drsgm\dist\i3drsgm-%version%-py3-none-win_amd64.whl
ren i3drsgm\dist\i3drsgm-%version%-py3-none-win_amd64.whl i3drsgm-%version%-py3-none-win_amd64-online.whl 
copy i3drsgm\dist\i3drsgm-%version%-py3-none-win_amd64-online.whl release\

