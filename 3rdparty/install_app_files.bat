@echo off

:: search for token in first argument
set token_found=false
if "%~1"=="" (
    :: token not stated in argument, look for it in token.txt file
    echo Reading PAT from 'token.txt'
    if exist "token.txt" (
        :: read github PAT from text file
        set /p token=< token.txt
        set token_found=true
    ) else (
        :: failed to file token.txt file
        echo Token file not found
    )
) else (
    :: token found in first argument, read token from argument
    set token=%~1
    set token_found=true
)

:: check token was found
if %token_found%==true (
    call i3drsgm\install_i3drsgm %token%

    :: Copy all 3rdparty dlls into single folder
    set "APP_FOLDER=..\i3drsgm\i3drsgm\app\"
    mkdir %APP_FOLDER%
    XCOPY i3drsgm\i3drsgm\i3drsgm-1.0.6\bin\*.dll %APP_FOLDER% /Y
    XCOPY i3drsgm\i3drsgm\i3drsgm-1.0.6\bin\*.exe %APP_FOLDER% /Y
    XCOPY i3drsgm\i3drsgm\opencv-4.5.0\opencv\build\x64\vc15\bin\opencv_world450.dll %APP_FOLDER% /Y
    XCOPY i3drsgm\i3drsgm\opencv-4.5.0\opencv\build\x64\vc15\bin\opencv_videoio_ffmpeg450_64.dll %APP_FOLDER% /Y
    XCOPY i3drsgm\i3drsgm\opencv-4.5.0\opencv\build\x64\vc15\bin\opencv_videoio_msmf450_64.dll %APP_FOLDER% /Y
    XCOPY i3drsgm\i3drsgm\phobosIntegration-1.0.54\bin\*.dll %APP_FOLDER% /Y
    XCOPY i3drsgm\i3drsgm\phobosIntegration-1.0.54\qt\*.dll %APP_FOLDER% /Y
) else (
    echo "Token not found"
    exit -1
)