import telebot
from geopy.geocoders import Nominatim
from datetime import datetime

from database import Data
import buttons

# Экземпляр для бота
bot = telebot.TeleBot('6200346206:AAEY7ye10drah0zJ1Pv7KJu1Yabk2zH_gQw')
geolocator = Nominatim(
    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36')


# Обработчик команды start
@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = message.from_user.id

    checker = Data().check_user(user_id)

    # Если есть пользователь в базе
    if checker:
        text = 'Выберите пункт меню'

        bot.send_message(user_id, text, reply_markup=buttons.main_menu())

    # Если нет пользователя в базе
    else:
        text = 'Добро пожаловать в службу доставки Tako🍗\nКак мы можем к Вам обращаться'

        bot.send_message(user_id, text)

        # Перекидываем на этап получения имени
        bot.register_next_step_handler(message, get_name)


# Этап получения имени
def get_name(message):
    username = message.text

    bot.send_message(message.from_user.id, 'Пожалуйста отправьте свой номер телефона', reply_markup=buttons.number_button())

    # Переход на этап получения номера телефона
    bot.register_next_step_handler(message, get_number, username)


# Этап получения номера телефона
def get_number(message, username):
    user_id = message.from_user.id

    # Если отправил номер в виде контакта
    if message.contact:
        user_number = message.contact.phone_number

        bot.send_message(user_id, 'Отправьте локацию', reply_markup=buttons.location_button())

        # Переход на этап получения локации
        bot.register_next_step_handler(message, get_location, username, user_number)

    # Если не в виде контакта
    else:
        bot.send_message(user_id, 'Пожалуйста отправьте номер пользуясь кнопкой')

        # Обратно перекинуть на этап получения номера
        bot.register_next_step_handler(message, get_number, username)


# Этап получения локации
def get_location(message, username, user_number):
    user_id = message.from_user.id

    # Если отправил локацию
    if message.location:
        # Перевод координат на формат адреса
        user_address = geolocator.reverse(f"{message.location.latitude}, {message.location.longitude}")
        # Регистрация
        Data().registration(user_id, username, user_number, str(user_address.address), datetime.now())

        bot.send_message(user_id, 'Успешно зарегистрированы\nВыберите пункт меню', reply_markup=buttons.main_menu())

    # Если не локация
    else:
        bot.send_message(user_id, 'Отправьте локацию используя кнопку')

        # Обратно на этап получения локации
        bot.register_next_step_handler(message, get_location, username, user_number)


# Обработчик текстовых сообщений и вся логика взаимодействия с пользователем
@bot.message_handler(content_types=['text'])
def text_message(message):
    user_id = message.from_user.id

    if message.text == 'Каталог':
        text = 'Выберите продукт'

        bot.send_message(user_id, text, reply_markup=buttons.catalog_button())

    elif message.text == 'Связаться с нами':
        text = 'Наш номер : +998992278877'
        bot.send_message(user_id, text)

    elif message.text in Data().show_all_products():
        about_product = Data().get_current_product(message.text)

        bot.send_message(user_id,
                         f'{about_product[0]}\nЦена: {about_product[1]}\nОписание:{about_product[2]}\n\nВыберите количество:',
                         reply_markup=buttons.count_button())

        # Переход на этап выбора количества
        bot.register_next_step_handler(message, get_pr_count, message.text)

    elif message.text == 'Корзина':
        user_cart = Data().show_user_cart(user_id)
        text = 'Ваша корзина\n\n'

        for i in user_cart:
            text += f'{i[1]} : {i[2]} = {i[3]}\n'

        bot.send_message(user_id, text, reply_markup=buttons.delete_from_cart_button(user_id))

        # Переход на этап для работы с корзиной
        bot.register_next_step_handler(message, work_with_cart)


# Этап для работы с корзиной
def work_with_cart(message):
    user_id = message.from_user.id

    if message.text == 'Назад':
        bot.send_message(user_id, 'ВЫберите продукт', reply_markup=buttons.catalog_button())

    elif message.text.starstwith('-'):
        Data().delete_product_from_cart(message.text[2:], user_id)

        bot.send_message(user_id, 'Продукт удален из корзины', reply_markup=buttons.catalog_button())

    elif message.text == 'Оформить заказ ':
        bot.send_message(user_id, 'Выберите удобное для вас время: ', reply_markup= buttons.time_order())

    elif message.text == 'Очистить корзину':
        Data.clear_user_cart(user_id)

        bot.send_message(user_id, 'Корзина очищена', reply_markup=buttons.catalog_button())


# Этап получения названия продукта
# Этап получения количества продукта и сохранения в корзину
def get_pr_count(message, product):
    product_count = message.text
    user_id = message.from_user.id

    if product_count.isnumeric:
        text = 'Продукт успешно добавлен'
        # Добавляем в корзину
        Data().add_to_cart(user_id, product, int(product_count))

        bot.send_message(user_id, text, reply_markup=buttons.catalog_button())

    else:
        text = 'Выберите количество используя кнопки'

        bot.send_message(user_id, text)

        # Обратно на этап выбора количества
        bot.register_next_step_handler(message, get_pr_count, product)


# Этап оформления заказа
def get_all_order(message):
    user_id = message.from_user.id
    if message.text == 'Оформить доставку':
        text = 'Выберите удобное для Вас время:'
        bot.send_message(user_id, text, reply_markup=buttons.time_order())

    else:
        text = 'Выберите время используя кнопки'
        bot.send_message(user_id, text)

        bot.register_next_step_handler(message, order_confirm)





# Этап подтверждения заказа
def order_confirm(message):
    user_id = message.from_user.id
    if message.text == 'В ближайщее время':
        text = 'Отправьте локацию'
        bot.send_message(user_id, text, reply_markup=buttons.location_button())

bot.polling()
