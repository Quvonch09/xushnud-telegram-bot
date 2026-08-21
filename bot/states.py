from aiogram.fsm.state import State, StatesGroup

class OrderStates(StatesGroup):
    waiting_for_link = State()
    waiting_for_reaction_emoji = State()
    waiting_for_poll_option = State()
    waiting_for_quantity = State()
    waiting_for_confirmation = State()

class PaymentStates(StatesGroup):
    waiting_for_screenshot = State()

class AdminStates(StatesGroup):
    waiting_for_add_balance_user_id = State()
    waiting_for_add_balance_amount = State()
    waiting_for_payment_approve_amount = State()
    waiting_for_card_number = State()
    waiting_for_card_comment = State()
    waiting_for_start_message = State()

