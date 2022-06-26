# Вступительное задание в Летнюю Школу Бэкенд Разработки Яндекса 2022

## Общее
Здание сделано на ```Flask``` и ```PostgreSQL```.

## Запуск

#### Общее
Для запуска нужен ```PostgreSQL```.

#### Установка переменных окружения
```$ export APP_SETTINGS="config.Config"```

```$ export DATABASE_URL="postgresql://USERNAME:PASSWORD@localhost/DB_NAME"```

#### Development
```$ flask run```
Запускается по умолчанию на [127.0.0.1:5000](http://127.0.0.1:5000/).

#### Production
```$ waitress-serve --port=80 --call app:create_app``` 
(default IP is ```0.0.0.0```) Проверить можно по [localhost](http://localhost:80/).

Или ```$ python main.py```.

## Запуск с помощью Docker

В ```docker-compose.yaml``` установить логин, пароль и название БД. 
Выполнить ```$ docker-compose up``` в папке с проектом.