import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hbold

from data.config import MASTERS
from loader import dp
from utils.db_api.commands import add_reviews


@dp.callback_query_handler(text="reviews")
async def reviews_send(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Напишите ваш отзыв:")
    await state.set_state("reviews")

@dp.message_handler(state="reviews")
async def reviews_update(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    name = message.from_user.full_name
    reviews = message.text
    await add_reviews(telegram_id, name, reviews)

    for master in MASTERS:
        try:
            await dp.bot.send_message(master, f"Отзыв от: {hbold(name)}.\n{reviews}")
        except Exception as err:
            logging.exception(err)

    await message.answer("Спасибо! Приходите еще!")
    await state.finish()