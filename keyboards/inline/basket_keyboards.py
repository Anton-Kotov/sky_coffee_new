from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

time_cd = CallbackData("time", "time")
your_time_cd = CallbackData("your", "time")

async def basket_select():
    markup = InlineKeyboardMarkup(row_width=2)

    drop = InlineKeyboardButton(text="Очистить корзину", callback_data="drop")
    markup.insert(drop)

    pay = InlineKeyboardButton(text="Перейти к оплате", callback_data="pay")
    markup.insert(pay)

    return markup

paid_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Оплатил",
                callback_data="paid")
        ],
        [
            InlineKeyboardButton(
                text="Отмена",
                callback_data="cancel")
        ],
    ]
)

async def time_select():
    markup = InlineKeyboardMarkup(row_width=3)

    now = InlineKeyboardButton(text="В течении 10 мин.", callback_data=time_cd.new(time="В течении 10 мин."))
    markup.insert(now)

    hour = InlineKeyboardButton(text="Через 30 мин.", callback_data=time_cd.new(time="Через час"))
    markup.insert(hour)

    your_time = InlineKeyboardButton(text="Свой вариант", callback_data=your_time_cd.new(time="Свой вариант"))
    markup.insert(your_time)

    return markup

reviews = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Оставить отзыв",
                callback_data="reviews")
        ]
    ]
)




