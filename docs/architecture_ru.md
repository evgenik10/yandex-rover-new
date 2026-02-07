# Автономные мини-роверы на Repka Pi: архитектура MVP

## Оглавление
1. Краткая архитектура
2. BOM и питание
3. Подключение GPIO/UART/I2C/USB
4. Логика ровера и PDD
5. Computer Vision (4 камеры)
6. Сервер и веб-панель (RBAC)
7. REST API
8. Структура проекта
9. Деплой (ровер + сервер)
10. Тестирование и отладка
11. План v2

## 1) Краткая архитектура
- **Ровер (Python, headless):** state-machine, safety-first, датчики, CV, управление моторами, heartbeat/ACK к серверу.
- **Сервер (Flask + Gunicorn + Nginx):** REST API, RBAC, аудит, хранение статуса/событий.
- **UI:** тёмная панель, список роверов, 4 камеры (MVP заглушка под MJPEG), карта (Leaflet), команды AUTO/MANUAL/STOP.
- **Безопасность:** API token на ровер, seq_id + timestamp, soft delete, revocation токена, role-based endpoint checks.

**Чек-лист**
- [ ] mode_desired/mode_reported разведены
- [ ] link-loss => stop
- [ ] E-STOP аппаратный + софтовый

**Troubleshooting**
- Команды не исполняются: проверить seq_id/timestamp и clock drift.
- Частые остановки: увеличить фильтрацию сенсоров, но не отключать failsafe.

## 2) BOM и питание
| Компонент | Назначение | Альтернатива | Критерий выбора | Тест |
|---|---|---|---|---|
| Repka Pi | вычисления | RPi-like SBC | USB, UART, I2C, стабильность | stress + thermal |
| TB6612 | драйвер моторов | L298N | КПД/нагрев | тест тока/темп |
| NEO-M8N | GPS | NEO-6M | TTFF/HDOP | холодный старт |
| HC-SR04 | передний стоп-датчик | VL53L1X | цена/простота | стенд 20-200см |
| 4x USB камеры | обзор 360° | CSI + USB mix | latency/fps | v4l2 fps |
| INA219 | батарея/ток | INA226 | точность | сверка мультиметром |
| E-STOP | аварийная безопасность | n/a | fail-open/fail-safe | мгновенный стоп |
| DC-DC + fuse | питание | BEC | пульсации/перегрузка | осциллограф |

**Энергобюджет (грубо):** SBC 6-12W + 4 камеры 8-16W + моторы 20-80W пиково. Питание моторов и логики разделять, земля общая.

**Чек-лист**
- [ ] отдельная линия питания моторов
- [ ] fuse + TVS + bulk capacitors

**Troubleshooting**
- Перезагрузка SBC при старте мотора: разнести питание, добавить low-ESR конденсаторы.

## 3) Подключение
**ПРОВЕРИТЬ ПО ДОКУМЕНТАЦИИ Repka Pi** (гипотеза 40-pin совместимости).

### TB6612 (по умолчанию)
| Сигнал | GPIO |
|---|---|
| AIN1/AIN2 | 17/27 |
| PWMA | 18 (PWM) |
| BIN1/BIN2 | 23/24 |
| PWMB | 13 (PWM) |
| STBY | 22 |

PWM 1-20kHz, торможение — короткое замыкание плеч (аккуратно с нагревом).

### HC-SR04
TRIG=GPIO5, ECHO=GPIO6. **ECHO=5V, нужен делитель/level-shifter до 3.3V.**

### GPS UART
TX/RX: GPIO14/15, baud 9600/38400, включить UART в конфиге ОС.

### I2C
SDA/SCL: GPIO2/3 для IMU/INA.

### USB камеры
udev-алиасы `/dev/video-front|rear|left|right` по serial/path; проверка `v4l2-ctl --list-devices`.

**Чек-лист**
- [ ] level shifting для ECHO
- [ ] общая земля
- [ ] udev rules для стабильных имён

**Troubleshooting**
- Прыгают номера /dev/video*: закрепить по ID_PATH/ID_SERIAL через udev.

## 4) Логика ровера и PDD
PDD-state: `BOOT, IDLE, ON_TRACK, OFF_TRACK, RETURNING, OBSTACLE_STOP, HUMAN_STOP, STOP_SIGN_STOP, GPS_DEGRADED, LINK_LOSS, EMERGENCY_STOP, ERROR`.

Приоритет: **человек > препятствие > маршрут > скорость**. При любой неопределённости — stop/min-risk.

**Чек-лист**
- [ ] command TTL 1-2s
- [ ] sensor conflict => STOP

**Troubleshooting**
- Ложные HUMAN_STOP: поднять confidence threshold + ROI masking.

## 5) CV (4 камеры)
MVP: YOLOv8n/YOLO-nano в ONNX, инференс 5-10 FPS/камера с пропуском кадров. Если CPU не тянет: 2-4 FPS + сенсоры как safety baseline.

**Чек-лист**
- [ ] классы person/stop_sign/obstacle
- [ ] зоны риска по секторам

**Troubleshooting**
- Высокая задержка: снизить до 640x360, INT8 квантование.

## 6) Сервер и UI
Роли: admin/operator/viewer. Viewer read-only. Admin может удалять/восстанавливать rover.
Удаление: soft-delete (`is_deleted=true`), revoke token, rover уходит в архив.

**Чек-лист**
- [ ] аудит действий пользователя
- [ ] подтверждение опасных действий

**Troubleshooting**
- Viewer видит кнопки управления: скрыть в UI + проверить backend RBAC.

## 7) REST API (минимум)
- `GET /api/ui/rovers`
- `POST /api/rovers/{id}/command` (seq_id, timestamp, mode/manual)
- `POST /api/rover/{id}/heartbeat` (mode_reported, pdd_state, gps, battery, camera_status)
- `POST /api/rover/{id}/ack` (seq_id, ok/error)
- `DELETE /api/admin/rovers/{id}` soft-delete

Ошибки: 401/403/404/409/422/500.

**Чек-лист**
- [ ] токен на rover endpoints
- [ ] rate limit на команды

**Troubleshooting**
- Дубли команд: хранить last seq_id и отклонять replay.

## 8) Структура проекта
- `rover/*.py` — runtime ровера
- `server/*.py` — Flask app/API/models
- `server/templates|static` — UI
- `tests/` — юнит-тесты

## 9) Деплой
Ровер: SSH, enable UART/I2C, venv, `config.yaml`, systemd restart=always.
Сервер: Flask behind Gunicorn+Nginx+TLS, firewall/VPN.

## 10) Тестирование
- Юнит: геометрия/навигация.
- Моки сенсоров/камер.
- Security: viewer не может командовать.
- Полевой чеклист: низкая скорость, частые остановки, ручной override.

## 11) План v2
IMU+одометрия, ToF/LiDAR, RTK, SLAM, websocket streaming, ROS2 migration path.
