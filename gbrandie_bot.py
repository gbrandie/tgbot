from PIL import Image, ImageEnhance
import telebot
import os
import time
import env # это файл, в котором лежит ключ от телеграм бота


def read_file(file_name):
    with open(file_name, 'r') as file:
        return file.read()


def add_watermark_imp(image, watermark, opacity=1, wm_interval=0):
    assert opacity >= 0 and opacity <= 1
    if opacity < 1:
        if watermark.mode != 'RGBA':
            watermark = watermark.convert('RGBA')
        else:
            watermark = watermark.copy()
        alpha = watermark.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
        watermark.putalpha(alpha)
    layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
    layer.paste(watermark, (0, 0))
    return Image.composite(layer, image, layer)


def add_watermark(image_path, watermark_path):
    img = Image.open(image_path)
    watermark = Image.open(watermark_path)
    watermark = watermark.resize((200, 200), Image.ANTIALIAS)
    result = add_watermark_imp(img, watermark)
    new_path = image_path + '_' + '.png'
    result.save(new_path)
    return new_path


def clear_content(chat_id):
    try:
        for img in images[chat_id]:
            os.remove(img)
    except Exception as e:
        clear_content(chat_id)
    images[chat_id] = []


bot = telebot.TeleBot(env.TOKEN_BOT)
images = dict()


@bot.message_handler(content_types=['text'])
def start(message):
    if message.text in ['/go', 'start', '/start', 'Привет', '/help', 'привет']:
        bot.send_message(message.from_user.id, f"Добро пожаловать, {message.from_user.first_name}"
                                               f" {message.from_user.last_name}!\n\nДанный бот позволяет добавить "
                                               f"водяной знак на фотографию. Отправьте"
                                               f" одним сообщением два изображения:\n\n"
                                               f"1. Фото, на которое нужно нанести водяной знак.\n"
                                               f"2. Водяной знак.\n\n"
                                               f"Лучше оставить галочку на 'Compress image'\n"
                                               f"Хорошего пользования.")
        bot.register_next_step_handler(message, handle_docs_photo)
    else:
        commands = "\n".join(['/start','/help','/go','/hello','Привет','привет'])
        bot.send_message(message.from_user.id, f'Неверный запрос. Для работы с ботом доступны команды:\n\n{commands}')

@bot.message_handler(content_types=['photo'])
def handle_docs_photo(message):
    print(message.photo[:-2])
    images[str(message.chat.id)] = []
    try:
        file_info = bot.get_file(message.photo[len(message.photo) - 1].file_id)

        downloaded_file = bot.download_file(file_info.file_path)

        src = 'tmp/' + file_info.file_path

        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)

        bot.reply_to(message, "Фото добавлено")
        images[str(message.chat.id)].append(src)
    except Exception as e:
        bot.reply_to(message, e)

    print('img: ', images)
    reply_img = ''
    if len(images[str(message.chat.id)]) == 2:
        reply_img = add_watermark(images[str(message.chat.id)][1], images[str(message.chat.id)][0])
        images[str(message.chat.id)].append(reply_img)
        bot.send_photo(message.chat.id, open(reply_img, 'rb'))
        clear_content(str(message.chat.id))


bot.polling(none_stop=True, interval=0)
