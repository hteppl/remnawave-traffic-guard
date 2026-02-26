## remnawave-traffic-guard

<p align="left">
  <a href="https://github.com/hteppl/remnawave-traffic-guard/releases/"><img src="https://img.shields.io/github/v/release/hteppl/remnawave-traffic-guard.svg" alt="Release"></a>
  <a href="https://hub.docker.com/r/hteppl/remnawave-traffic-guard/"><img src="https://img.shields.io/badge/DockerHub-remnawave--traffic--guard-blue" alt="DockerHub"></a>
  <a href="https://github.com/hteppl/remnawave-traffic-guard/actions"><img src="https://img.shields.io/github/actions/workflow/status/hteppl/remnawave-traffic-guard/dockerhub-publish.yaml" alt="Build"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.12-blue.svg" alt="Python 3.12"></a>
  <a href="https://opensource.org/licenses/GPL-3.0"><img src="https://img.shields.io/badge/license-GPLv3-green.svg" alt="License: GPL v3"></a>
</p>

[English](README.md) | Русский

Мониторинг трафика пользователей [Remnawave](https://docs.rw), обнаружение аномалий и отправка уведомлений в Telegram.

## Возможности

- **Обнаружение всплесков** — Уведомление при превышении порога трафика за один интервал проверки
- **Контроль общего лимита** — Уведомление при превышении суммарного порога за скользящее окно
- **Часовые отчеты** — Периодические сводки в Telegram: активные пользователи, общий трафик, топ потребитель
- **Разбивка по серверам** — В уведомлениях отображаются топ-серверы по трафику для каждого пользователя
- **Telegram-уведомления** — HTML-форматированные алерты в канал/топик или личные сообщения админам
- **Масштаб 100k+ пользователей** — Redis-хэши с O(1) поиском и пакетной записью через pipeline
- **Мультиязычность** — Поддержка английского и русского языков
- **Docker** — Два контейнера (приложение + Redis) через Docker Compose

## Требования

- **Remnawave Panel** с добавленными пользователями
- **Remnawave API Token** — генерируется в настройках панели
- **Telegram Bot Token** — создайте через [@BotFather](https://t.me/BotFather)
- **Docker** и **Docker Compose**

## Настройка

Скопируйте [`.env.example`](.env.example) в `.env` и заполните значения:

```env
# Remnawave
REMNAWAVE_API_URL=https://panel.example.com
REMNAWAVE_API_KEY=remnawave_api_key

# Telegram (токен от @BotFather)
TELEGRAM_BOT_TOKEN=your_bot_token_here
# Chat ID (узнать через @username_to_id_bot)
TELEGRAM_CHAT_ID=123456789
# ID топика (для форумов, иначе оставить пустым)
TELEGRAM_TOPIC_ID=

INTERVAL_CHECK_ENABLED=true
# Интервал проверки трафика (минуты)
CHECK_INTERVAL_MINUTES=10
# Порог всплеска за один интервал (ГБ)
INTERVAL_THRESHOLD_GB=20

TOTAL_CHECK_ENABLED=true
# Скользящее окно для общего лимита (часы)
TOTAL_CHECK_HOURS=24
# Порог общего лимита (ГБ)
TOTAL_THRESHOLD_GB=100

HOURLY_STATS_ENABLED=true

# Язык уведомлений: en, ru
LANGUAGE=ru
# Часовой пояс
TIMEZONE=Europe/Moscow
# Формат времени: %d-день, %m-месяц, %Y-год, %H-час, %M-мин, %S-сек
TIME_FORMAT="%d.%m.%Y %H:%M:%S"
# Игнорировать разницу трафика ниже этого значения (ГБ)
MIN_TRAFFIC_GB=0.5
# Макс. серверов в уведомлении
TOP_NODES_LIMIT=5

# Пользователей на страницу API (макс. 1000)
API_PAGE_SIZE=1000

# URL Redis (данные сохраняются через Redis AOF)
REDIS_URL=redis://redis:6379/0
```

### Параметры

| Переменная               | Описание                                   | По умолчанию           | Обязательно |
|--------------------------|--------------------------------------------|------------------------|-------------|
| `REMNAWAVE_API_URL`      | Адрес API Remnawave                        | -                      | Да          |
| `REMNAWAVE_API_KEY`      | API токен Remnawave                        | -                      | Да          |
| `TELEGRAM_BOT_TOKEN`     | Токен бота (@BotFather)                    | -                      | Да          |
| `TELEGRAM_CHAT_ID`       | ID чата для уведомлений                    | -                      | Да          |
| `TELEGRAM_TOPIC_ID`      | ID топика (для форумов)                    | -                      | Нет         |
| `INTERVAL_CHECK_ENABLED` | Обнаружение всплесков за интервал          | `true`                 | Нет         |
| `CHECK_INTERVAL_MINUTES` | Интервал проверки (минуты)                 | `10`                   | Нет         |
| `INTERVAL_THRESHOLD_GB`  | Порог всплеска за интервал (ГБ)            | `20`                   | Нет         |
| `TOTAL_CHECK_ENABLED`    | Контроль общего лимита                     | `true`                 | Нет         |
| `TOTAL_CHECK_HOURS`      | Скользящее окно (часы)                     | `24`                   | Нет         |
| `TOTAL_THRESHOLD_GB`     | Порог общего лимита (ГБ)                   | `100`                  | Нет         |
| `HOURLY_STATS_ENABLED`   | Часовые отчеты                             | `true`                 | Нет         |
| `LANGUAGE`               | Язык уведомлений (`en`, `ru`)              | `en`                   | Нет         |
| `TIMEZONE`               | Часовой пояс                               | `Europe/Moscow`        | Нет         |
| `TIME_FORMAT`            | Формат времени                             | `%d.%m.%Y %H:%M:%S`    | Нет         |
| `MIN_TRAFFIC_GB`         | Мин. разница трафика для учета (ГБ)        | `0.5`                  | Нет         |
| `TOP_NODES_LIMIT`        | Макс. серверов в уведомлении               | `5`                    | Нет         |
| `API_PAGE_SIZE`          | Пользователей на страницу API (макс. 1000) | `1000`                 | Нет         |
| `REDIS_URL`              | URL подключения к Redis                    | `redis://redis:6379/0` | Нет         |

## Установка

### Docker (рекомендуется)

1. Создайте `docker-compose.yml`:

```yaml
services:
  remnawave-traffic-guard:
    image: hteppl/remnawave-traffic-guard:latest
    container_name: remnawave-traffic-guard
    restart: unless-stopped
    env_file:
      - .env
    depends_on:
      redis:
        condition: service_healthy

  redis:
    image: redis:8-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - traffic-guard-redis-data:/data
    healthcheck:
      test: [ 'CMD', 'redis-cli', 'ping' ]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  traffic-guard-redis-data:
```

2. Настройте `.env`:

```bash
cp .env.example .env
nano .env
```

3. Запустите:

```bash
docker compose up -d && docker compose logs -f
```

### Ручная установка

1. Клонируйте репозиторий:

```bash
git clone https://github.com/hteppl/remnawave-traffic-guard.git
cd remnawave-traffic-guard
```

2. Создайте виртуальное окружение (рекомендуется):

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# или
.venv\Scripts\activate     # Windows
```

3. Установите зависимости:

```bash
pip install -r requirements.txt
```

4. Настройте `.env`:

```bash
cp .env.example .env
```

5. Убедитесь, что Redis запущен и `REDIS_URL` указывает на него, затем:

```bash
python -m src
```

## Принцип работы

1. **Запуск** — Подключение к Redis, отправка стартового уведомления в Telegram с текущими порогами

2. **Периодическая проверка** — Каждые `CHECK_INTERVAL_MINUTES` минут сервис запрашивает всех пользователей через
   Remnawave API и сравнивает текущий трафик со снимками в Redis

3. **Обнаружение всплесков** — Если прирост трафика пользователя за один интервал превышает `INTERVAL_THRESHOLD_GB`,
   отправляется уведомление с разбивкой по серверам

4. **Контроль общего лимита** — Если суммарный трафик пользователя за `TOTAL_CHECK_HOURS` часов превышает
   `TOTAL_THRESHOLD_GB`, отправляется уведомление

5. **Обновление снимков** — После каждой проверки все снимки пользователей записываются в Redis

6. **Часовые отчеты** — На границе каждого часа отправляется сводка: всего/активных пользователей, потребленный трафик,
   топ пользователь и количество алертов

## Telegram-уведомления

### Подключение

1. Создайте бота через [@BotFather](https://t.me/BotFather) и получите токен
2. Узнайте свой chat ID через [@username_to_id_bot](https://t.me/username_to_id_bot)
3. Добавьте бота в чат/группу
4. Укажите `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHAT_ID` в `.env`

### Типы уведомлений

| Событие             | Описание                                  |
|---------------------|-------------------------------------------|
| **Всплеск трафика** | Пользователь превысил порог за интервал   |
| **Общий лимит**     | Пользователь превысил суммарный порог     |
| **Часовая сводка**  | Периодический отчет с общей статистикой   |
| **Запуск сервиса**  | Мониторинг запущен с текущими настройками |

### Логи

```bash
docker compose logs -f
```

## Лицензия

[GNU General Public License v3.0](LICENSE)
