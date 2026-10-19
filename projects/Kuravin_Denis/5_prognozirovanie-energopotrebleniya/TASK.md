# 5. Прогнозирование энергопотребления здания

**Участник:** Денис Куравин

> Положите сюда файлы проекта (код, отчёт `REPORT.md`/PDF, docker-compose, скриншоты)
> и откройте Pull Request. После того как PR примут, проект автоматически
> отметится галкой в README и на сайте.

## Что нужно сделать
Собирать показания счётчиков и датчиков, прогнозировать потребление на ближайшие часы и находить необычные пики.

## Технологии
Python, Kafka, XGBoost/LightGBM, Pandas, ClickHouse/TimescaleDB, Grafana, FastAPI, Docker

## Архитектура
IoT/time-series streaming + forecasting service + anomaly detection + dashboard

## Паттерны
Observer, Strategy, Repository, Pipeline, Circuit Breaker

## Что показать в отчёте
1. Цель и проблема проекта
2. требования и ограничения
3. описание входных и выходных данных
4. архитектурная схема (желательно C4: Context/Container/Component)
5. описание всех микросервисов и границ ответственности
6. Kafka topics, producers/consumers, формат сообщений и consumer groups
7. схема БД/аналитического хранилища и индексы
8. API с примерами запросов и ответов
9. минимум 3 применённых паттерна: место применения + зачем + схема/код
10. Dockerfile/docker-compose и инструкция запуска
11. тестирование и результаты
12. скриншоты работающего pipeline/dashboard/API
13. для ML: датасет, preprocessing, модель, метрики, baseline, результаты и ограничения
14. для RL: environment, state/action/reward, алгоритм, график обучения, итоговые метрики и сравнение
15. выводы и распределение работы
