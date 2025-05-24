offfor /d %%i in (*) do (  if exist "%%i\migrations" (    echo Cleaning migrations in %%i    cd "%%i\migrations"    del /q *.py    del /q *.pyc    echo.     cd ..\..  ))
