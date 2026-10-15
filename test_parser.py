from app.survey_parser import parse_survey_text, parse_grades
from app.texts import SURVEY_TEMPLATE


def test_grades():
    assert parse_grades("9, 10, 11") == [9, 10, 11]
    assert parse_grades("5-8") == [5, 6, 7, 8]
    assert parse_grades("5-6, 9") == [5, 6, 9]


def test_template_is_valid():
    title, grades, questions, errors = parse_survey_text(SURVEY_TEMPLATE)
    assert not errors and grades == [9, 10, 11] and len(questions) == 2
    assert questions[0].type == "choice" and questions[1].type == "text"


def test_errors():
    *_, errors = parse_survey_text("Sarlavha: X\nSinflar: 3\n1. a\n- b")
    assert errors
