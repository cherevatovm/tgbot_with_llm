import telebot
import requests
import jsons
from Class_ModelResponse import ModelResponse

# Замените 'YOUR_BOT_TOKEN' на ваш токен от BotFather
API_TOKEN = 'YOUR_BOT_TOKEN'
bot = telebot.TeleBot(API_TOKEN)

# Словарь для хранения контекста пользователей
context_for_users = {}

# Команды
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "Привет! Я ваш Telegram бот.\n"
        "Доступные команды:\n"
        "/start - вывод всех доступных команд\n"
        "/model - выводит название используемой языковой модели\n"
        "/clear - очистка контекста текущего диалога\n"
        "Отправьте любое сообщение, и я отвечу с помощью LLM модели."
    )
    bot.reply_to(message, welcome_text)


@bot.message_handler(commands=['model'])
def send_model_name(message):
    # Отправляем запрос к LM Studio для получения информации о модели
    response = requests.get('http://localhost:1234/v1/models')

    if response.status_code == 200:
        model_info = response.json()
        model_name = model_info['data'][0]['id']
        bot.reply_to(message, f"Используемая модель: {model_name}")
    else:
        bot.reply_to(message, 'Не удалось получить информацию о модели.')


@bot.message_handler(commands=['clear'])
def clear_context(message):
    user_id = message.chat.id
    if user_id in context_for_users:
        del context_for_users[user_id]
        bot.reply_to(message, "Контекст диалога очищен.")
    else:
        bot.reply_to(message, "Контекст уже пуст.")


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.chat.id
    user_query = message.text

    # Инициализация контекста для нового пользователя
    if user_id not in context_for_users:
        context_for_users[user_id] = []

    # Добавление сообщение пользователя в контекст
    context_for_users[user_id].append({"role": "user", "content": user_query})

    # Создание запроса для модели
    request = {
        "messages": context_for_users[user_id]
    }
    
    response = requests.post(
        'http://localhost:1234/v1/chat/completions',
        json=request
    )

    if response.status_code == 200:
        model_response = jsons.loads(response.text, ModelResponse)
        bot_reply = model_response.choices[0].message.content
        
        context_for_users[user_id].append({"role": "assistant", "content": bot_reply})

        bot.reply_to(message, bot_reply)
    else:
        bot.reply_to(message, 'Произошла ошибка при обращении к модели.')


# Запуск бота
if __name__ == '__main__':
    bot.polling(none_stop=True)
