from aiogram.fsm.state import State, StatesGroup


class AdminAuth(StatesGroup):
    waiting_password = State()


class AdminCategoryStates(StatesGroup):
    waiting_name = State()
    waiting_emoji = State()
    waiting_new_name = State()
    waiting_new_emoji = State()
    confirm_delete = State()


class AdminProductStates(StatesGroup):
    waiting_category = State()
    waiting_name = State()
    waiting_description = State()
    waiting_price = State()
    waiting_photo = State()
    confirm_delete = State()
    edit_select_field = State()
    edit_name = State()
    edit_description = State()
    edit_price = State()
    edit_photo = State()


class AdminSettingsStates(StatesGroup):
    edit_about = State()
    edit_phone = State()
    edit_instagram = State()
    edit_telegram = State()
    edit_address = State()
    edit_schedule = State()
    edit_shop_name = State()
    edit_welcome_text = State()
    edit_order_info = State()
    change_password = State()
    confirm_password = State()
