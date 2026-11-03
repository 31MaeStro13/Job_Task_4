import os
from typing import Optional
from dotenv import load_dotenv

from agno.agent import Agent
from agno.models.google import Gemini
from agno.models.openai import OpenAIChat

from app.models import ProductInput, ProductCardOutput
from app.validator import find_missing_specs

# Загружаем переменные окружения
load_dotenv()

SYSTEM_INSTRUCTIONS = """
Ты — ведущий технический копирайтер и эксперт по B2B-каталогам контрольно-измерительных приборов и автоматики (КИПиА).
Твоя задача: на основе сырых входных данных сформировать черновик карточки товара для промышленного маркетплейса / интернет-магазина.

СТРОГИЕ ТРЕБОВАНИЯ И ОГРАНИЧЕНИЯ (ZERO-HALLUCINATION & SPECS):
1. SEO-ЗАГОЛОВОК (seo_title):
   - Длина: строго ДО 70 символов с пробелами.
   - Формат: [Тип прибора] [Модель] [Производитель] [Ключевой параметр].
   - Без кликбейта, только емкая техническая суть.

2. SEO-ОПИСАНИЕ (seo_description):
   - Объем: строго 800–1200 символов с пробелами.
   - Стиль: профессиональный B2B (для инженеров КИПиА, главных энергетиков и специалистов по закупкам).
   - Структура: назначение, принцип работы, сферы применения, конструктивные преимущества и соответствие промышленным стандартам.

3. ХАРАКТЕРИСТИКИ (specs_formatted):
   - КАТЕГОРИЧЕСКИЙ ЗАПРЕТ НА ГАЛЛЮЦИНАЦИИ! Все значения параметров берутся ТОЛЬКО из входных данных.
   - Запрещено додумывать диапазоны, класс точности, климатику или питание.
   - Если характеристика важна для данного типа прибора, но отсутствует во входе — явно указывать значение: "данных нет".

4. ПОИСКОВЫЕ ЗАПРОСЫ (search_queries):
   - Ровно 3–5 целевых поисковых запросов под Яндекс и Google (коммерческие и номенклатурные, например: "манометр дм 02 купить", "манометр манотомь 1.6 мпа цена").

5. КОММЕРЧЕСКИЙ БЛОК (commercial_block):
   - target_audience: перечислить целевые отрасли (ЖКХ, котельные, теплосети, нефтегаз, пищепром и т.д.).
   - solved_tasks: 3-5 конкретных производственных задач, решаемых прибором.

6. ОТСУТСТВУЮЩИЕ ИЛИ НЕПОЛНЫЕ ПОЛЯ (missing_or_unclear_fields):
   - Если в исходных данных не хватает важных технических сведений (например, нет климатического исполнения, степени защиты IP, межповерочного интервала или типа резьбы), прямо перечисли их в этом списке с пометкой для менеджера по закупкам.
"""


def get_model(provider: Optional[str] = None):
    """Фабрика инициализации модели на основе переменных окружения."""
    selected_provider = (provider or os.getenv("LLM_PROVIDER", "gemini")).lower()

    if selected_provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        model_id = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
        if not api_key:
            raise ValueError(
                "Не найден GEMINI_API_KEY. Укажите его в .env файле или переменных окружения."
            )
        return Gemini(id=model_id, api_key=api_key)

    elif selected_provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        model_id = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        if not api_key:
            raise ValueError(
                "Не найден OPENAI_API_KEY. Укажите его в .env файле или переменных окружения."
            )
        return OpenAIChat(id=model_id, api_key=api_key)

    else:
        raise ValueError(
            f"Неподдерживаемый провайдер '{selected_provider}'. Доступны: 'gemini', 'openai'."
        )


def create_product_agent(provider: Optional[str] = None) -> Agent:
    """Создает и настраивает Agno Agent для генерации карточки товара."""
    model = get_model(provider)
    return Agent(
        name="B2B Product Card Specialist",
        model=model,
        instructions=SYSTEM_INSTRUCTIONS,
        output_schema=ProductCardOutput,
        structured_outputs=True,
    )


def generate_product_card(
    product: ProductInput,
    provider: Optional[str] = None
) -> ProductCardOutput:
    """
    Генерирует готовую карточку товара с детерминированным контролем пропусков.
    """
    # 1. Предварительный детерминированный поиск отсутствующих базовых характеристик
    missing_deterministic = find_missing_specs(product)

    # 2. Формируем контекст для LLM
    agent = create_product_agent(provider)
    prompt = f"""
ВХОДНЫЕ ДАННЫЕ О ПРИБОРЕ:
Название: {product.name}
Производитель: {product.manufacturer}
Характеристики: {product.specs}
Описание / паспорт: {product.description or 'Не предоставлено'}

ПРЕДВАРИТЕЛЬНО ОБНАРУЖЕННЫЕ ПРОПУСКИ БАЗОВЫХ ПАРАМЕТРОВ:
{', '.join(missing_deterministic) if missing_deterministic else 'Все базовые параметры найдены'}

Сформируй карточку товара строго по схеме ProductCardOutput с соблюдением всех лимитов (Title <= 70 симв., Описание 800-1200 симв.).
"""

    response = agent.run(prompt)
    card: ProductCardOutput = response.content

    # 3. Синхронизируем детерминированные пропуски с замечаниями модели
    combined_missing = set(card.missing_or_unclear_fields or [])
    for m in missing_deterministic:
        combined_missing.add(f"Отсутствует характеристика: {m}")
    card.missing_or_unclear_fields = sorted(list(combined_missing))

    return card
