from aiogram.fsm.state import State, StatesGroup


class SurveyState(StatesGroup):
    waiting_fio = State()
    waiting_grade_num = State()
    waiting_grade_letter = State()
    waiting_survey_pick = State()
    answering = State()


class SupportState(StatesGroup):
    waiting_message = State()


class AdminState(StatesGroup):
    waiting_survey_text = State()
    confirm_broadcast = State()
