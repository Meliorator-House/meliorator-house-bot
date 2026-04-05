# Telegram AI Bot - Инструкция по развертыванию на Vercel

## Что это?

Это полностью готовый Telegram-бот с поддержкой ИИ, который работает 24/7 на Vercel.

**Возможности:**
- ✅ Отвечает на сообщения с помощью ИИ
- ✅ Показывает эффект печати
- ✅ Редактирует сообщения
- ✅ Помнит контекст разговора
- ✅ Команды: `/start`, `/help`, `/clear`

## Шаг 1: Подготовка на GitHub

### 1.1 Создать репозиторий на GitHub

1. Зайти на https://github.com
2. Нажать "New repository"
3. Назвать его `telegram-bot` (или любое другое имя)
4. Выбрать "Public"
5. Нажать "Create repository"

### 1.2 Загрузить файлы

```bash
# Скопировать этот архив в папку
cd telegram_bot_vercel

# Инициализировать git
git init
git add .
git commit -m "Initial commit: Telegram AI Bot"
git branch -M main
git remote add origin https://github.com/ВАШ_ЮЗЕР/telegram-bot.git
git push -u origin main
```

Замените `ВАШ_ЮЗЕР` на ваше имя пользователя GitHub.

## Шаг 2: Развертывание на Vercel

### 2.1 Подключить Vercel

1. Зайти на https://vercel.com
2. Нажать "Sign Up" (или "Log In" если уже есть аккаунт)
3. Выбрать "Continue with GitHub"
4. Авторизоваться

### 2.2 Импортировать проект

1. На Vercel нажать "New Project"
2. Выбрать "Import Git Repository"
3. Найти репозиторий `telegram-bot`
4. Нажать "Import"

### 2.3 Добавить переменные окружения

1. В форме "Environment Variables" добавить:

```
TELEGRAM_BOT_TOKEN = 8309759443:AAGPd06QlyYYEykZO2CxPpo4lfS6jzkPsDU
BUILT_IN_FORGE_API_URL = https://api.manus.im
BUILT_IN_FORGE_API_KEY = ваш_ключ_api
```

2. Нажать "Deploy"

### 2.4 Ждать развертывания

Vercel автоматически:
- Установит зависимости из `requirements.txt`
- Развернет код
- Даст вам URL вроде: `https://telegram-bot-xyz.vercel.app`

## Шаг 3: Настроить Telegram вебхук

После развертывания нужно сказать Telegram куда отправлять сообщения.

### 3.1 Получить URL вашего бота

На Vercel в разделе "Deployments" найти URL вашего проекта. Он будет выглядеть так:
```
https://telegram-bot-xyz.vercel.app
```

### 3.2 Установить вебхук

Выполнить эту команду (замените на ваш URL):

```bash
curl -X POST https://api.telegram.org/bot8309759443:AAGPd06QlyYYEykZO2CxPpo4lfS6jzkPsDU/setWebhook \
  -H "Content-Type: application/json" \
  -d '{"url": "https://telegram-bot-xyz.vercel.app/api/webhook"}'
```

Или просто откройте в браузере (замените на ваш URL):
```
https://api.telegram.org/bot8309759443:AAGPd06QlyYYEykZO2CxPpo4lfS6jzkPsDU/setWebhook?url=https://telegram-bot-xyz.vercel.app/api/webhook
```

### 3.3 Проверить вебхук

```bash
curl https://api.telegram.org/bot8309759443:AAGPd06QlyYYEykZO2CxPpo4lfS6jzkPsDU/getWebhookInfo
```

Должно вывести что-то вроде:
```json
{
  "ok": true,
  "result": {
    "url": "https://telegram-bot-xyz.vercel.app/api/webhook",
    "has_custom_certificate": false,
    "pending_update_count": 0
  }
}
```

## Шаг 4: Тестирование

1. Найти вашего бота в Telegram (по имени)
2. Отправить `/start`
3. Бот должен ответить приветствием
4. Написать любой вопрос
5. Бот должен ответить с помощью ИИ

## Структура файлов

```
telegram_bot_vercel/
├── api/
│   └── webhook.py          # Основной обработчик вебхука
├── bot.py                  # Локальный бот (для тестирования)
├── requirements.txt        # Зависимости Python
├── vercel.json            # Конфигурация Vercel
├── .env.example           # Пример переменных окружения
└── SETUP.md               # Эта инструкция
```

## Как это работает?

1. **Telegram отправляет сообщение** → `/api/webhook`
2. **Vercel обрабатывает** → `webhook.py`
3. **Бот отправляет запрос** → LLM API
4. **LLM отвечает** → Бот получает ответ
5. **Бот отправляет ответ** → Telegram
6. **Пользователь видит ответ** ✅

## Команды бота

- `/start` - Начать
- `/help` - Помощь
- `/clear` - Очистить историю разговора

## Решение проблем

### Бот не отвечает

1. Проверить переменные окружения в Vercel
2. Проверить вебхук: `getWebhookInfo`
3. Посмотреть логи в Vercel → Deployments → Logs

### Ошибка "Unauthorized"

- Проверить `TELEGRAM_BOT_TOKEN` - он правильный?
- Проверить `BUILT_IN_FORGE_API_KEY` - он правильный?

### Timeout

- Увеличить `maxDuration` в `vercel.json` (максимум 60 секунд)

## Локальное тестирование

Если хотите тестировать локально перед развертыванием:

```bash
# Установить зависимости
pip install -r requirements.txt

# Установить переменные окружения
export TELEGRAM_BOT_TOKEN="8309759443:AAGPd06QlyYYEykZO2CxPpo4lfS6jzkPsDU"
export BUILT_IN_FORGE_API_URL="https://api.manus.im"
export BUILT_IN_FORGE_API_KEY="ваш_ключ"

# Запустить бота
python3 bot.py
```

## Дальнейшее развитие

Вы можете добавить:
- Сохранение истории в БД
- Обработку файлов и изображений
- Интерактивные кнопки
- Интеграцию с другими сервисами
- Аналитику использования

## Поддержка

Если что-то не работает:
1. Проверить логи в Vercel
2. Убедиться что все переменные окружения установлены
3. Проверить вебхук статус
4. Перезагрузить проект в Vercel

## Готово! 🎉

Ваш Telegram-бот теперь работает 24/7 на Vercel!
