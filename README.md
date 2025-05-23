# 🔍 Telegram Monitor Bot: Ваш Бдительный Страж Telegram-Просторов!

Устали пропускать важные объявления о недвижимости или другие ключевые сообщения в Telegram-чатах и каналах? Этот бот — ваш персональный ассистент, который неустанно следит за указанными источниками и мгновенно уведомляет вас о появлении сообщений с заданными ключевыми словами.

## ✨ Ключевые Возможности

-   👀 **Мониторинг в реальном времени:** Отслеживание сообщений в неограниченном количестве чатов и каналов.
-   🔔 **Мгновенные уведомления:** Получайте оповещения сразу же, как только появится сообщение с вашими ключевыми словами.
-   ⚙️ **Гибкое управление:** Легко добавляйте новые чаты, управляйте ключевыми словами для каждого из них индивидуально.
-   📋 **Удобный список:** Просматривайте все отслеживаемые чаты с возможностью быстрого редактирования или удаления.
-   🧹 **Автоматическая очистка:** Старые записи и уведомления могут автоматически удаляться для поддержания порядка.

## 🚀 Первоначальная Настройка и Запуск

Перед тем как начать пользоваться всеми прелестями бота, необходимо выполнить один важный шаг:

### **ВАЖНО: Получение сессии Telegram (`session.session`)**

Для того чтобы бот мог отслеживать сообщения от вашего имени, ему необходим файл сессии `session.session`. Этот файл создается при успешной аутентификации вашего Telegram-аккаунта через библиотеку Telethon.

1.  **Локальный запуск скрипта-аутентификатора:**
    *   Вам потребуется запустить основной скрипт мониторинга (или специальный скрипт для генерации сессии, если он предусмотрен) на вашем локальном компьютере. Например, это может быть команда `python telegram_monitor.py`.
    *   При первом запуске скрипт попытается подключиться к Telegram API.

2.  **Ввод кода от Telegram:**
    *   Telegram запросит номер телефона (если не указан в коде/конфиге) и затем код подтверждения, который будет отправлен вам в Telegram (в "Сохраненные сообщения" или в чат с Telegram).
    *   Введите этот код в консоль, где запущен скрипт.
    *   Если у вас включена двухфакторная аутентификация, также потребуется ввести пароль от нее.

3.  **Генерация `session.session`:**
    *   После успешной аутентификации в директории, откуда был запущен скрипт, будет автоматически создан файл с именем `ВАШЕ_ИМЯ_СЕССИИ.session` (например, `my_account.session` или просто `session.session`, в зависимости от того, как вы назвали сессию в коде).
    *   **Этот файл `session.session` необходимо поместить в корневую директорию проекта с ботом и с монитором, чтобы он мог использовать эту сессию для своей работы.**

‼️ **Крайне важно:** Не завершайте этот активный сеанс в настройках вашего Telegram-аккаунта (в разделе «Устройства» или «Активные сеансы»). Завершение сеанса сделает файл `session.session` недействительным, и потребуется повторная аутентификация (повторение шагов 1-3).

## 🤖 Инструкция по Использованию (Админ-бот)

Взаимодействие с ботом происходит через специальный админ-интерфейс, доступный только вам.

1.  🚀 **Запуск:** Отправьте команду `/start` админ-боту.
2.  🔑 **Авторизация:** Доступ к боту имеют только авторизованные пользователи (т.е. вы).
3.  🛠️ **Основные функции админ-панели:**
    *   Добавление новых чатов для мониторинга.
    *   Управление ключевыми словами для каждого чата.
    *   Просмотр списка отслеживаемых чатов.
    *   Удаление чатов из мониторинга.

### ➕ Добавление чата для мониторинга

1.  В главном меню админ-бота нажмите кнопку "➕ Добавить чат".
2.  **Перешлите любое сообщение** из чата или канала, который вы хотите добавить.
    *   Если это **канал**, сообщение *должно быть* от имени самого канала (не репост в чат, а именно оригинальное сообщение из канала).
    *   Если это **чат**, подойдет любое сообщение из него.
3.  После этого бот запросит вас ввести ключевые слова через запятую, по которым будет осуществляться поиск в данном чате/канале.

### 📝 Управление ключевыми словами

1.  В главном меню выберите чат из списка отслеживаемых.
2.  Нажмите кнопку "📝 Изменить ключевые слова".
3.  Введите новый список ключевых слов через запятую. Старые ключевые слова будут заменены.

### ❌ Удаление чата из мониторинга

1.  В главном меню выберите чат из списка отслеживаемых.
2.  Нажмите кнопку "❌ Удалить чат".
3.  Подтвердите свое намерение удалить чат из списка мониторинга.

## 🔒 Ограничения и Важные Моменты

-   👤 **Эксклюзивный доступ:** Только вы (администратор) можете управлять ботом и получать уведомления.
-   👁️ **Область видимости:** Бот может мониторить только те чаты и каналы, участником которых является аккаунт, чей `session.session` используется.
-   🔄 **Активность сессии:** Помните о необходимости поддерживать активной сессию Telegram, с которой был сгенерирован `session.session` (см. раздел "Первоначальная Настройка").

## 🛠️ Технический Стек

### 🖥️ Backend
-   Python 3.8+
-   **Telethon:** Мощная библиотека для взаимодействия с Telegram API на низком уровне (используется для мониторинга).
-   **aiogram 3.x:** Современный асинхронный фреймворк для создания Telegram-ботов (используется для админ-панели).
-   **MongoDB:** Гибкая NoSQL база данных для хранения информации о чатах, уведомлениях и настройках.
-   **asyncio:** Основа для асинхронной работы всего приложения.

### 🏗️ Архитектура
-   **Асинхронность во всем:** Максимальное использование `async/await` для неблокирующих операций.
-   **Микросервисный подход (концептуально):** Логическое разделение сервиса мониторинга (на Telethon) и админ-панели (на aiogram).
-   **Event-driven система:** Реакция на события (новые сообщения, команды пользователя).
-   **Модульная структура:** Код организован для легкого понимания и расширения.

### 🗂️ База данных (MongoDB)
-   `channels`: Коллекция для хранения информации об отслеживаемых чатах и их ключевых словах.
-   `notifications`: История отправленных уведомлений.
-   `processed_messages`: Журнал ID обработанных сообщений для избежания дубликатов.
-   `messages`: Сообщения, связанные с работой админ-бота (например, для пошаговых диалогов).

### 🛡️ Безопасность
-   **Конфигурация через `.env`:** Чувствительные данные (API ключи, ID администратора) хранятся в переменных окружения.
-   **Ограничение доступа к админ-боту:** Только авторизованный пользователь может управлять ботом.
-   **Безопасное хранение API ключей:** Не допускается хардкод чувствительных данных.
-   **Валидация входящих данных:** Проверка корректности данных, получаемых от пользователя.

### 📈 Масштабируемость и Оптимизация
-   **Динамическое управление чатами:** Добавление и удаление чатов без перезапуска основного сервиса мониторинга.
-   **Автоматическая очистка старых данных:** Механизмы для предотвращения переполнения БД.
-   **Оптимизированные запросы к БД:** Эффективное использование индексов и запросов.
-   **Асинхронная обработка:** Способность обрабатывать множество событий одновременно без блокировок.

## ✨ Особенности Реализации
-   🚀 **Полностью асинхронная обработка:** От получения сообщений до взаимодействия с БД и отправки уведомлений.
-   📄 **Пагинация:** Удобный просмотр больших списков отслеживаемых чатов в админ-панели.
-   🔄 **Автоматическое обновление:** Список отслеживаемых чатов и их ключевые слова подхватываются сервисом мониторинга "на лету".
-   🧠 **Умная система обработки ключевых слов:** Эффективный поиск по содержимому сообщений.
-   ✍️ **Логирование:** Запись всех ключевых действий и ошибок для отладки и анализа.
-   🚨 **Обработка ошибок и уведомления:** Система старается корректно обрабатывать исключительные ситуации и информировать администратора при необходимости.

