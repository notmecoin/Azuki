@echo off
:loop
echo Запуск бота...
py -3.10 main.py
echo Бот вылетел. Перезапуск через 5 секунд...
timeout /t 5
goto loop
