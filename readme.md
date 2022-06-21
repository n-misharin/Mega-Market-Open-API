# Вступительное задание в Летнюю Школу Бэкенд Разработки Яндекса 2022
## Запуск
### Общее
```$export APP_SETTINGS="config.Config"```

```$export DATABASE_URL="postgresql://POSTGRES_USERNAME:PASS@localhost/DB_NAME"```
### Dev
```$flask run```
### Production
```$waitress-serve --port=80 --call app:create_app``` 
(default IP is ```0.0.0.0```)
Проверить можно по [localhost](http://localhost:80/)