@echo off
rem Устанавливаем имя образа и контейнера
set IMAGE_NAME=my-tg-bot
set CONTAINER_NAME=tg-bot

rem Проверяем наличие Docker
docker -v >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Docker не установлен или не работает. Пожалуйста, установите Docker.
    pause
    exit /b
)

rem Проверяем, существует ли образ
docker images | findstr /i %IMAGE_NAME% >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Образ не найден. Запуск сборки Docker образа.
    docker build -t %IMAGE_NAME% .
)

rem Проверяем, существует ли контейнер
docker ps -a | findstr /i %CONTAINER_NAME% >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Контейнер не найден. Создание нового контейнера.
    docker run -d --name %CONTAINER_NAME% --env-file .env %IMAGE_NAME%
) else (
    echo Контейнер найден. Перезапуск контейнера.
    docker start %CONTAINER_NAME%
)

echo Бот успешно запущен!
pause
