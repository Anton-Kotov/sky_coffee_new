from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InputMedia

from keyboards.inline.basket_keyboards import basket_select, time_select
from keyboards.inline.menu_keyboards import basket_add_cd, basket_cd, make_order_keyboard
from loader import dp
from utils.db_api.commands import update_user_basket, select_user, update_user_current_price, update_total_spent, \
    update_user_num
from utils.db_api.menu_commands import get_item


@dp.callback_query_handler(basket_add_cd.filter())
async def add_basket(callback: types.CallbackQuery, callback_data: dict, state: FSMContext):

    telegram_id = callback.from_user.id
    user = await select_user(telegram_id)
    if len(user.basket) <= 1200:
        await update_user_num(telegram_id, user.num + 1)
        data = await state.get_data()
        order1 = data["order"]
        order_first = data["order_first"]
        order = f"{user.basket}{user.num + 1}) {order1}"
        current_price = data["price"] + user.current_price
        await update_user_basket(telegram_id, order)
        await update_user_current_price(telegram_id, current_price)
        main = callback_data.get("main")
        category = callback_data.get("category")
        subcategory = callback_data.get("subcategory")
        await state.finish()
        async with state.proxy() as data:
            data["volume_price"] = 0
            data["milk_price"] = 0
        item = await get_item(main_code=main, category_code=category, subcategory_code=subcategory)
        markup = await make_order_keyboard(callback, callback_data, main=main, category=category,
                                           subcategory=subcategory, state=state)
        photo = InputMedia(media=(item[0].photo), caption=order_first)
        await callback.message.edit_media(media=photo, reply_markup=markup)
    else:
        await callback.answer(text="Корзина переполнена", show_alert=True)
    await callback.answer()

@dp.callback_query_handler(basket_cd.filter())
async def show_basket(callback: types.CallbackQuery, state: FSMContext):
    markup = await basket_select()
    telegram_id = callback.from_user.id
    user = await select_user(telegram_id)
    text = f"{user.basket}\n\nВсего к оплате {user.current_price}₽"
    photo = InputMedia(media="https://ibb.co/Z8qP9KY", caption=text)
    await callback.message.edit_media(media=photo, reply_markup=markup)


@dp.callback_query_handler(text="drop")
async def drop_basket(callback: types.CallbackQuery, state: FSMContext):

    telegram_id = callback.from_user.id
    await update_user_num(telegram_id, 0)
    await update_user_basket(telegram_id, "")
    await update_user_current_price(telegram_id, 0)
    await state.finish()
    markup = await basket_select()
    text = f"Всего к оплате 0₽"
    photo = InputMedia(media="https://ibb.co/Z8qP9KY", caption=text)
    await callback.message.edit_media(media=photo, reply_markup=markup)
    # await callback.answer(text="Корзина очищена", show_alert=True)

@dp.callback_query_handler(text="pay")
async def pay_basket(callback: types.CallbackQuery, state: FSMContext):
    telegram_id = callback.from_user.id
    user = await select_user(telegram_id)
    total_spent = user.total_spent
    amount = user.current_price
    await update_total_spent(telegram_id, total_spent=total_spent + amount)
    markup = await time_select()
    await callback.message.answer(text="Выберите, когда хотите забрать заказ.\n"
                                       "(в течении 10 мин., через 30 мин. или укажите сами.)", reply_markup=markup)
    await state.set_state("pay")
    await callback.answer()

