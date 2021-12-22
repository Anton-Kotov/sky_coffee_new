from typing import Union
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InputMedia
from aiogram.utils.markdown import hbold

from keyboards.default.menu import menu
from keyboards.inline.menu_keyboards import subcategories_keyboard, \
    menu_cd, main_keyboard, categories_keyboard, make_order_keyboard, \
    adds_keyboard
from loader import dp
from utils.db_api.add_commands import get_add
from utils.db_api.menu_commands import get_item



@dp.message_handler(text="МЕНЮ📖")
async def show_main_menu(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["telegram_id"] = message.from_user.id

    await message.answer("Выбери, что ты хочешь купить.\n"
                         "Для покупки используй кнопки.")
    await message.answer(text="Для завершения заказа\nзайди в КОРЗИНУ внизу", reply_markup=menu)
    await list_main(message)


async def list_main(message: Union[types.Message, types.CallbackQuery], **kwargs):
    markup = await main_keyboard(message)

    if isinstance(message, types.Message):
        #await message.answer("Наше меню", reply_markup=markup)
        await message.answer_photo(
            photo="https://crossroadsoflife.ru/wp-content/uploads/2018/03/kofe.jpg",
            caption="Наше меню",
            reply_markup=markup)

    elif isinstance(message, types.CallbackQuery):
        call = message
        #await call.message.edit_reply_markup(markup)
        photo = InputMedia(media="https://crossroadsoflife.ru/wp-content/uploads/2018/03/kofe.jpg", caption="Наше меню")
        await call.message.edit_media(media=photo, reply_markup=markup)

async def list_categories(callback: types.CallbackQuery, main, state:FSMContext, **kwargs):
    markup = await categories_keyboard(callback, main)
    # await callback.message.edit_reply_markup(markup)
    photo = InputMedia(media="https://crossroadsoflife.ru/wp-content/uploads/2018/03/kofe.jpg", caption="Наше меню")
    await callback.message.edit_media(media=photo, reply_markup=markup)
    await callback.answer()


async def list_subcategories(callback: types.CallbackQuery, main, category, state: FSMContext, **kwargs):

    markup = await subcategories_keyboard(callback, main, category)
    # await callback.message.edit_reply_markup(markup)
    photo = InputMedia(media="https://crossroadsoflife.ru/wp-content/uploads/2018/03/kofe.jpg", caption="Наше меню")
    await callback.message.edit_media(media=photo, reply_markup=markup)
    await callback.answer()
    await state.finish()

async def list_order(callback: types.CallbackQuery, callback_data: dict,
                     main, category, subcategory, state: FSMContext, **kwargs):

    item = await get_item(main_code=main, category_code=category, subcategory_code=subcategory)

    async with state.proxy() as data:                           # формируем меню добавок (исключения)
        if item[0].volume == "порция":
            data["volume"] = data.get("volume", "Порция")
        elif item[0].subcategory_name == "Мороженое":
            data["volume"] = data.get("volume", "100 гр.")
        else:
            data["volume"] = data.get("volume", item[0].volume[:3] + " мл.")

        if (item[0].main_name == "Чай" and item[0].subcategory_name != "Матча-латте") \
            or item[0].subcategory_name == "Эспрессо" or item[0].subcategory_name == "Гранола":

            data["milk"] = data.get("milk", "Нет")
        else:
            data["milk"] = data.get("milk", "Коровье")

        data["adds"] = data.get("adds", "Ничего")
        data["volume_price"] = data.get("volume_price", 0)
        data["milk_price"] = data.get("milk_price", 0)
        data["add_price"] = data.get("add_price", 0)


        name = callback_data["name"]

        if name != "0":                                     # смотрим какая добавка к заказу выбрана
            category_add = callback_data["category_add"]
            add = await get_add(category_add, name[1:])
            if name[0] == "1":

                data["volume"] = name[1:] + " мл."
                if name[1:] == "200":
                    data["volume_price"] = item[0].p200
                elif name[1:] == "300":
                    data["volume_price"] = item[0].p300
                elif name[1:] == "400":
                    data["volume_price"] = item[0].p400
                elif name[1:] == "500":
                    data["volume_price"] = item[0].p500

            elif name[0] == "2":
                data["milk"] = name[1:]
                data["milk_price"] = add[0].price
            elif name[0] == "3":
                if data["adds"] != "Ничего":
                    data["adds"] = data["adds"] + " + " + name[1:]
                    data["syrop"] = name[1:]
                    data["add_price"] = data["add_price"] + add[0].price
                else:
                    data["adds"] = name[1:]
                    data["syrop"] = name[1:]
                    data["add_price"] = add[0].price
            elif name[0] == "4":
                if data["adds"] != "Ничего":
                    data["adds"] = data["adds"] + " + " + name[1:]
                    data["other"] = name[1:]
                    data["add_price"] = data["add_price"] + add[0].price
                else:
                    data["adds"] = name[1:]
                    data["other"] = name[1:]
                    data["add_price"] = add[0].price

        volume = data["volume"]
        milk = data["milk"]
        adds = data["adds"]
        if data["volume_price"] == 0:
            price = item[0].price + data["milk_price"] + data["add_price"]
        else:
            price = data["volume_price"] + \
                    data["milk_price"] + data["add_price"]

        data["price"] = price


    markup = await make_order_keyboard(callback, callback_data, main=main, category=category, subcategory=subcategory, state=state)


    if "молоко" in item[0].adds:
        text = '\n'.join([f"{item[0].main_name}: {hbold(item[0].subcategory_name)}",
                          f"объемом: {hbold(volume)}",
                          f"молоко: {hbold(milk)}",
                          f"добавить: {hbold(adds)}\n",
                          f"Цена: {hbold(price)}₽\n\n"])
    else:
        text = '\n'.join([f"{item[0].main_name}: {item[0].subcategory_name}",
                          f"объемом: {hbold(volume)}",
                          f"добавить: {hbold(adds)}\n",
                          f"Цена: {hbold(price)}₽\n\n"])

    async with state.proxy() as data:
        data["order"] = text

    photo = InputMedia(media=(item[0].photo), caption=text)
    await callback.message.edit_media(media=photo, reply_markup=markup)
    await callback.answer()

async def list_adds(callback: types.CallbackQuery, main, category, subcategory, category_add, state: FSMContext, **kwargs):

    markup = await adds_keyboard(main=main, category=category, subcategory=subcategory, category_add=category_add)
    item = await get_item(main_code=main, category_code=category, subcategory_code=subcategory)
    data = await state.get_data()

    text = data["order"]

    photo = InputMedia(media=(item[0].photo), caption=text)
    await callback.message.edit_media(media=photo, reply_markup=markup)
    await callback.answer()


@dp.callback_query_handler(menu_cd.filter())
async def navigate(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    current_level = callback_data.get('level')
    callback_data: dict
    main = callback_data.get('main')
    category = callback_data.get('category')
    subcategory = callback_data.get('subcategory')
    # item_id = int(callback_data.get('item_id'))
    category_add = callback_data.get('category_add')
    # add_id = int(callback_data.get('add_id'))
    state: FSMContext

    levels = {
                "0": list_main,
                "1": list_categories,
                "2": list_subcategories,
                "3": list_order,
                "4": list_adds
             }
    current_level_function = levels[current_level]

    await current_level_function(
        call,
        callback_data=callback_data,
        main=main,
        category=category,
        subcategory=subcategory,
        category_add=category_add,
        state=state
    )
    await call.answer()

