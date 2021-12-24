import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hlink, hcode, hbold

from data.config import ADMINS
from keyboards.inline.basket_keyboards import paid_keyboard, your_time_cd, time_cd, reviews
from loader import dp
from utils.db_api.commands import select_user, update_user_basket, update_user_current_price, update_user_num
from utils.misc.qiwi import Payment, NoPaymentFound, NotEnoughMoney



@dp.callback_query_handler(time_cd.filter(), state="pay")
async def time(callback: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await callback.answer()
    telegram_id = callback.from_user.id
    user = await select_user(telegram_id)
    amount = user.current_price

    async with state.proxy() as data:
        data["time"] = callback_data["time"]

    payment = Payment(amount=amount)
    payment.create()

    await callback.message.answer(
        "\n".join(
            [
                f"Для получения заказа перейдите по ссылке.",
                f"ПОСЛЕ завершения оплаты нажмите кнопку 'Оплатил'.",
                f"Всего к оплате: {amount}₽",
                "",
                hlink("Ссылка для оплаты", url=payment.invoice),
                "ID платежа:",
                hcode(payment.id)
            ]
        ),
        reply_markup=paid_keyboard
    )
    await state.set_state("qiwi")
    await state.update_data(payment=payment)

@dp.callback_query_handler(your_time_cd.filter(), state="pay")
async def your_time(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text="Введите время, когда заберете заказ:")
    await state.set_state("your")


@dp.message_handler(state="your")
async def pay(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    user = await select_user(telegram_id)
    amount = user.current_price
    async with state.proxy() as data:
        data["time"] = message.text

    payment = Payment(amount=amount)
    payment.create()

    await message.answer(
        "\n".join(
            [
                f"Для получения заказа перейдите по ссылке.",
                f"ПОСЛЕ завершения оплаты нажмите кнопку 'Оплатил'.",
                f"Всего к оплате: {amount}₽",
                "",
                hlink("Ссылка для оплаты", url=payment.invoice),
                "ID платежа:",
                hcode(payment.id)
            ]
        ),
        reply_markup=paid_keyboard
    )
    await state.set_state("qiwi")
    await state.update_data(payment=payment)


@dp.callback_query_handler(text="cancel", state="qiwi")
async def cancel_payment(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Отменено")
    await state.finish()
    await callback.answer()

@dp.callback_query_handler(text="paid", state="qiwi")
async def approve_payment(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    payment: Payment = data.get("payment")
    try:
        payment.check_payment()
    except NoPaymentFound:
        await callback.message.answer("Транзакция не найдена.")
        return
    except NotEnoughMoney:
        await callback.message.answer("Оплаченная сумма меньше необходимой.")
        return

    else:
        await callback.message.answer("Успешно оплачено.\n"
                                      "Заберите заказ в указанное время.")
        await callback.message.answer("Для следующего заказа нажмите кнопку - МЕНЮ.\n"
                                      "Выможете оствить отзыв.\n"
                                      "Нам очень важно ваше мнение о нас!\n", reply_markup=reviews)
        await callback.answer()

        telegram_id = callback.from_user.id
        user = await select_user(telegram_id)
        amount = user.current_price
        data = await state.get_data()
        time = data["time"]
        text = f"{user.basket}\nПокупатель заберет заказ: {hbold(time)}\n" \
               f"Всего оплачено: {hbold(amount)}₽"

        await update_user_basket(telegram_id, text)
        for admin in ADMINS:
            try:
                user = await select_user(telegram_id)
                await dp.bot.send_message(admin, user.basket)
            except Exception as err:
                logging.exception(err)

    await callback.message.edit_reply_markup()
    await state.finish()

    await update_user_num(telegram_id, 0)
    await update_user_basket(telegram_id, "")
    await update_user_current_price(telegram_id, 0)
    await callback.answer()

