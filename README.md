## hw05_final

Yatube - это социальная сеть блогеров которая позволяет публиковать свои и комментировать чужие посты, а также подписываться(отписываться) на(от) интересующих авторов. Разработан по классической MVT архитектуре. Используются пагинация постов и кэширование. Регистрация реализована с верификацией данных. Написаны тесты, проверяющие работу сервиса.

## Запускаем проект:
Клонируем репозиторий и переходим в него в командной строке:

```
git clone https://github.com/Calyps0l/hw05_final.git
```
Cоздаем и активируем виртуальное окружение:

```
python -m venv venv
```
Устанавливаем зависимости:

```
pip install -r requirements.txt
```
Выполняем миграции:

```
python manage.py migrate
```
Запускаем проект:

```
python3 manage.py runserver
```
