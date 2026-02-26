## remnawave-traffic-guard

<p align="left">
  <a href="https://github.com/hteppl/remnawave-traffic-guard/releases/"><img src="https://img.shields.io/github/v/release/hteppl/remnawave-traffic-guard.svg" alt="Release"></a>
  <a href="https://hub.docker.com/r/hteppl/remnawave-traffic-guard/"><img src="https://img.shields.io/badge/DockerHub-remnawave--traffic--guard-blue" alt="DockerHub"></a>
  <a href="https://github.com/hteppl/remnawave-traffic-guard/actions"><img src="https://img.shields.io/github/actions/workflow/status/hteppl/remnawave-traffic-guard/dockerhub-publish.yaml" alt="Build"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.12-blue.svg" alt="Python 3.12"></a>
  <a href="https://opensource.org/licenses/GPL-3.0"><img src="https://img.shields.io/badge/license-GPLv3-green.svg" alt="License: GPL v3"></a>
</p>

English | [Русский](README.ru.md)

Monitor users traffic from [Remnawave](https://docs.rw), detect anomalies, and send Telegram alerts.

## Features

- **Interval Spike Detection** — Alerts when a user exceeds a traffic threshold within a single check interval
- **Total Limit Detection** — Alerts when a user exceeds a cumulative traffic threshold over a rolling time window
- **Hourly Stats Reports** — Periodic Telegram summaries with active users, total traffic, and top consumer
- **Per-Node Breakdown** — Alerts include top nodes by traffic for each flagged user
- **Telegram Notifications** — HTML-formatted alerts to a channel/topic or admin DMs
- **100k+ Users Scale** — Redis-backed O(1) snapshot lookups with pipelined bulk writes
- **Multi-Language** — Supports English and Russian notification templates
- **Docker Ready** — Two-container deployment (app + Redis) with Docker Compose

## Prerequisites

Before you begin, ensure you have the following:

- **Remnawave Panel** with users configured
- **Remnawave API Token** — Generate from your Remnawave panel settings
- **Telegram Bot Token** — Create with [@BotFather](https://t.me/BotFather)
- **Docker** and **Docker Compose** installed

## Configuration

Copy [`.env.example`](.env.example) to `.env` and fill in your values:

```env
# Remnawave panel URL and API key
REMNAWAVE_API_URL=https://panel.example.com/api
REMNAWAVE_API_KEY=remnawave_api_key

# Telegram bot token from @BotFather
TELEGRAM_BOT_TOKEN=your_bot_token_here
# Chat ID (get from @username_to_id_bot)
TELEGRAM_CHAT_ID=123456789
# Forum topic ID (leave empty for regular chats)
TELEGRAM_TOPIC_ID=

INTERVAL_CHECK_ENABLED=true
# How often to check traffic (minutes)
CHECK_INTERVAL_MINUTES=10
# Alert if user exceeds this in one interval (GB)
INTERVAL_THRESHOLD_GB=20

TOTAL_CHECK_ENABLED=true
# Rolling window for total check (hours)
TOTAL_CHECK_HOURS=24
# Alert if user exceeds this over the window (GB)
TOTAL_THRESHOLD_GB=100

HOURLY_STATS_ENABLED=true

# Supported languages: en, ru
LANGUAGE=en
# Timezone (e.g. UTC, Europe/Moscow, America/New_York)
TIMEZONE=Europe/Moscow
# Time format: %d-day, %m-month, %Y-year, %H-hour, %M-min, %S-sec
TIME_FORMAT="%d.%m.%Y %H:%M:%S"
# Ignore traffic diffs below this value (GB)
MIN_TRAFFIC_GB=0.5
# Max nodes shown per alert
TOP_NODES_LIMIT=5

# Users per API page (max 1000)
API_PAGE_SIZE=1000

# Redis URL (data is persisted via Redis AOF)
REDIS_URL=redis://redis:6379/0
```

### Configuration Reference

| Variable                 | Description                                  | Default              | Required |
|--------------------------|----------------------------------------------|----------------------|----------|
| `REMNAWAVE_API_URL`      | Remnawave API endpoint                       | -                    | Yes      |
| `REMNAWAVE_API_KEY`      | Remnawave API token                          | -                    | Yes      |
| `TELEGRAM_BOT_TOKEN`     | Telegram bot token from @BotFather           | -                    | Yes      |
| `TELEGRAM_CHAT_ID`       | Chat ID for notifications                    | -                    | Yes      |
| `TELEGRAM_TOPIC_ID`      | Forum topic ID (for supergroups with topics) | -                    | No       |
| `INTERVAL_CHECK_ENABLED` | Enable per-interval spike detection          | `true`               | No       |
| `CHECK_INTERVAL_MINUTES` | Traffic check interval in minutes            | `10`                 | No       |
| `INTERVAL_THRESHOLD_GB`  | Spike alert threshold per interval (GB)      | `20`                 | No       |
| `TOTAL_CHECK_ENABLED`    | Enable rolling total limit detection         | `true`               | No       |
| `TOTAL_CHECK_HOURS`      | Rolling window for total check (hours)       | `24`                 | No       |
| `TOTAL_THRESHOLD_GB`     | Total traffic alert threshold (GB)           | `100`                | No       |
| `HOURLY_STATS_ENABLED`   | Enable hourly stats reports                  | `true`               | No       |
| `LANGUAGE`               | Notification language (`en`, `ru`)           | `en`                 | No       |
| `TIMEZONE`               | Timezone for timestamps                      | `Europe/Moscow`      | No       |
| `TIME_FORMAT`            | Time format for timestamps                   | `%d.%m.%Y %H:%M:%S` | No       |
| `MIN_TRAFFIC_GB`         | Ignore traffic diffs below this value (GB)   | `0.5`                | No       |
| `TOP_NODES_LIMIT`        | Max nodes shown per alert                    | `5`                  | No       |
| `API_PAGE_SIZE`          | Users per API page (max 1000)                | `1000`               | No       |
| `REDIS_URL`              | Redis connection URL                         | `redis://redis:6379/0` | No     |

## Installation

### Docker (recommended)

1. Create the `docker-compose.yml`:

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
      test: ['CMD', 'redis-cli', 'ping']
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  traffic-guard-redis-data:
```

2. Create and configure your environment file:

```bash
cp .env.example .env
nano .env  # or use your preferred editor
```

3. Start the containers:

```bash
docker compose up -d && docker compose logs -f
```

### Manual Installation

1. Clone the repository:

```bash
git clone https://github.com/hteppl/remnawave-traffic-guard.git
cd remnawave-traffic-guard
```

2. Create a virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create and configure your environment file:

```bash
cp .env.example .env
```

5. Make sure Redis is running and `REDIS_URL` points to it, then run:

```bash
python -m src
```

## How It Works

1. **Startup** — Connects to Redis, sends a startup notification to Telegram with current thresholds

2. **Periodic Check** — Every `CHECK_INTERVAL_MINUTES` minutes, fetches all users from the Remnawave API and compares current traffic against previous snapshots stored in Redis

3. **Spike Detection** — If a user's traffic increase within a single interval exceeds `INTERVAL_THRESHOLD_GB`, sends an alert with per-node traffic breakdown

4. **Total Limit Detection** — If a user's cumulative traffic over `TOTAL_CHECK_HOURS` hours exceeds `TOTAL_THRESHOLD_GB`, sends an alert

5. **Snapshot Update** — After each check, all user snapshots are written to Redis for the next cycle

6. **Hourly Reports** — On each hour boundary, sends a summary with total/active users, traffic consumed, top user, and alert count

## Telegram Notifications

### Setup

1. Create a bot with [@BotFather](https://t.me/BotFather) and get the token
2. Get your chat ID from [@username_to_id_bot](https://t.me/username_to_id_bot)
3. Add the bot to your chat/group
4. Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env`

### Notification Types

| Event              | Description                                      |
|--------------------|--------------------------------------------------|
| **Traffic Spike**  | User exceeded interval threshold                 |
| **Total Limit**    | User exceeded rolling total threshold            |
| **Hourly Stats**   | Periodic report with traffic summary             |
| **Service Start**  | Monitoring started with current configuration    |

### Logs

Monitor logs to diagnose issues:

```bash
docker compose logs -f
```

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).
