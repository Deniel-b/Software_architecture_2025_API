# 5. RL-агент для игры в клеточный dungeon crawler

**Участник:** Эля Варганова

> Положите сюда файлы проекта (код, отчёт `REPORT.md`/PDF, docker-compose, скриншоты)
> и откройте Pull Request. После того как PR примут, проект автоматически
> отметится галкой в README и на сайте.

## Что нужно сделать
Создать среду игры и обучить агента исследовать карту, собирать награды и избегать ловушек/врагов.

## Технологии
Python, Gymnasium, PyTorch, Stable-Baselines3, Pygame, Kafka, MLflow, Docker

## Архитектура
Game simulator + RL trainer + inference service + telemetry collector

## Паттерны
State, Strategy, Observer, Command, Factory, Event Sourcing

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
