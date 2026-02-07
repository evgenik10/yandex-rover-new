# Yandex Rover New — Fleet MVP

MVP-проект для управления несколькими мини-роверами на базе Repka Pi:
- runtime на ровере (Python, safety-first state-machine)
- сервер и веб-панель (Flask + SQLite)
- REST API для heartbeat/команд/ACK

## Что уже есть в UI
- Профиль админа: добавление новых admin/moder пользователей
- Выпадающее меню выбора ровера + действия (добавить/проверить связь/удалить)
- Добавление ровера по IP (admin)
- Удаление ровера (admin, soft-delete)
- Ручное управление: вперёд / назад / влево / вправо / стоп
- Кнопка "Открыть крышку" (команда на доп. мотор актуатора)
- Проверка связи с индикацией: ✔ (онлайн) / ✖ (офлайн)
- Карта с текущей позицией выбранного ровера (Leaflet + OSM)

## Быстрый старт

### 1) Сервер
```bash
cd server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Откройте `http://127.0.0.1:8000`.

Логин по умолчанию:
- `admin`
- `admin123` (обязательно поменять)

### 2) Тесты
```bash
python -m pytest -q
```

## Структура
- `rover/` — модули ровера (motors, gps, sensors, vision, navigation, main)
- `server/` — Flask приложение, API, шаблоны и статика
- `deploy/` — примеры systemd и nginx
- `docs/architecture_ru.md` — архитектура, BOM, wiring, PDD, troubleshooting

## Важно по железу
Pin mapping в проекте указан как гипотеза совместимости с 40-pin Raspberry Pi форм-фактором и **должен быть проверен по официальной документации Repka Pi**.

## Roadmap
- более строгий backend RBAC
- rate-limit + replay protection по `seq_id`
- подтверждение команд через ACK + timeout retries
- переход на WebRTC/RTSP для видео
