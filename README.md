# film-bot
## Описание
Телеграмм бот для поиска фильма по коду

## Deploy
```bash
docker build -t maksard99/film-bot:<version> .  
docker push maksard99/film-bot:<version>
```
На сервере
```bash
docker run --env-file=.env-film-bot --name=film-bot -d maksard99/film-bot:<version>
```