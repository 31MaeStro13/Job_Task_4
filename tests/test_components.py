import pytest
from app.models import ProductInput, ProductCardOutput, CommercialBlock, SpecItem
from app.validator import find_missing_specs, validate_card_output
from app.formatter import format_as_markdown, format_as_text, format_as_json


def test_product_input_validation():
    data = {
        "name": "Манометр DM 02",
        "manufacturer": "Манотомь",
        "specs": {"диапазон": "0-1.6 МПа"},
        "description": "Тестовое описание"
    }
    prod = ProductInput(**data)
    assert prod.name == "Манометр DM 02"
    assert prod.manufacturer == "Манотомь"
    assert prod.specs["диапазон"] == "0-1.6 МПа"


def test_product_input_empty_name_fails():
    with pytest.raises(ValueError):
        ProductInput(name="   ", manufacturer="Тест", specs={})


def test_find_missing_specs():
    prod = ProductInput(
        name="Манометр DM 02",
        manufacturer="Манотомь",
        specs={
            "диапазон измерений": "0–1,6 МПа",
            "класс точности": "1,5",
            "присоединение": "G1/2"
        },
        description="Механический манометр"
    )
    missing = find_missing_specs(prod)
    # Питание и выходной сигнал отсутствуют для механического манометра
    assert "питание" in missing
    assert "выходной сигнал / интерфейс" in missing
    # А эти присутствуют
    assert "диапазон измерений" not in missing
    assert "класс точности / погрешность" not in missing


def test_formatters():
    card = ProductCardOutput(
        seo_title="Купить манометр DM 02 Манотомь | Цена и характеристики",
        seo_description="A" * 850,
        specs_formatted=[
            SpecItem(name="диапазон", value="0-1.6 МПа"),
            SpecItem(name="питание", value="данных нет"),
        ],
        search_queries=["манометр dm 02", "купить манометр манотомь", "манометр 1.6 мпа"],
        commercial_block=CommercialBlock(
            target_audience="Промышленные предприятия и котельные",
            solved_tasks=["Контроль давления воды и газа"]
        ),
        missing_or_unclear_fields=["питание", "выходной сигнал"]
    )
    md = format_as_markdown(card)
    assert "# Купить манометр" in md
    assert "данных нет" in md
    assert "⚠️ питание" in md

    txt = format_as_text(card)
    assert "SEO-ЗАГОЛОВОК:" in txt

    json_str = format_as_json(card)
    assert '"seo_title":' in json_str


def test_validator_card_constraints():
    # 1. Валидная карточка
    card_ok = ProductCardOutput(
        seo_title="Манометр DM 02 Манотомь 1.6 МПа",
        seo_description="B" * 950,
        specs_formatted=[],
        search_queries=["q1", "q2", "q3"],
        commercial_block=CommercialBlock(target_audience="test", solved_tasks=["t1"]),
        missing_or_unclear_fields=[]
    )
    assert len(validate_card_output(card_ok)["warnings"]) == 0

    # 2. Невалидная длина
    card_bad = ProductCardOutput(
        seo_title="Очень длинный заголовок, который превышает допустимый правилами лимит в 70 символов для SEO заголовка",
        seo_description="Слишком короткий текст",
        specs_formatted=[],
        search_queries=["q1", "q2", "q3"],
        commercial_block=CommercialBlock(target_audience="test", solved_tasks=["t1"]),
        missing_or_unclear_fields=[]
    )
    warnings = validate_card_output(card_bad)["warnings"]
    assert any("Превышение длины SEO-заголовка" in w for w in warnings)
    assert any("выходит за рамки ТЗ" in w for w in warnings)
