from typing import Dict, List, Set
from app.models import ProductInput, ProductCardOutput

# Типовые базовые характеристики для приборов КИПиА
ESSENTIAL_INSTRUMENT_SPECS: Dict[str, List[str]] = {
    "диапазон измерений": ["диапазон", "предел", "шкала", "range"],
    "класс точности / погрешность": ["класс точности", "погрешность", "точность", "accuracy"],
    "присоединение к процессу": ["присоединение", "резьба", "фланец", "штуцер", "connection"],
    "температурный режим": ["температура", "климатическое", "т_окр", "temperature"],
    "выходной сигнал / интерфейс": ["выходной сигнал", "интерфейс", "hart", "rs-485", "4-20"],
    "питание": ["питание", "напряжение", "power", "в ="],
}


def find_missing_specs(input_data: ProductInput) -> List[str]:
    """
    Детерминированный поиск отсутствующих базовых параметров КИПиА.
    Проверяет ключи specs и текст описания на наличие упоминаний.
    """
    existing_text = (
        " ".join(f"{k} {v}" for k, v in input_data.specs.items()) + " " + (input_data.description or "")
    ).lower()

    missing: List[str] = []
    for spec_name, aliases in ESSENTIAL_INSTRUMENT_SPECS.items():
        found = any(alias in existing_text for alias in aliases)
        if not found:
            missing.append(spec_name)
    return missing


def validate_card_output(output: ProductCardOutput) -> Dict[str, List[str]]:
    """
    Детерминированная валидация ограничений ТЗ по сгенерированной карточке.
    """
    warnings: List[str] = []
    
    # 1. Проверка длины SEO-заголовка
    if len(output.seo_title) > 70:
        warnings.append(
            f"Превышение длины SEO-заголовка: {len(output.seo_title)} симв. (лимит 70)"
        )

    # 2. Проверка объема SEO-описания
    desc_len = len(output.seo_description)
    if desc_len < 800 or desc_len > 1200:
        warnings.append(
            f"Объем SEO-описания {desc_len} симв. выходит за рамки ТЗ (800–1200 симв.)"
        )

    # 3. Проверка количества поисковых запросов
    queries_count = len(output.search_queries)
    if queries_count < 3 or queries_count > 5:
        warnings.append(
            f"Количество поисковых запросов ({queries_count}) не соответствует диапазону 3–5"
        )

    return {"warnings": warnings}
