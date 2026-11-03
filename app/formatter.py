import json
from app.models import ProductCardOutput


def format_as_markdown(card: ProductCardOutput) -> str:
    """Форматирует карточку товара в читаемый и структурированный Markdown."""
    lines = []
    
    # SEO Title
    lines.append(f"# {card.seo_title}")
    lines.append("")
    
    # Commercial Block
    lines.append("## Коммерческий блок")
    lines.append(f"**Целевая аудитория:** {card.commercial_block.target_audience}")
    lines.append("")
    lines.append("**Решаемые задачи:**")
    for task in card.commercial_block.solved_tasks:
        lines.append(f"- {task}")
    lines.append("")
    
    # SEO Description
    lines.append("## Описание товара")
    lines.append(card.seo_description)
    lines.append("")
    lines.append(f"*Символов с пробелами: {len(card.seo_description)}*")
    lines.append("")
    
    # Specs
    lines.append("## Технические характеристики")
    lines.append("| Параметр | Значение |")
    lines.append("| :--- | :--- |")
    for spec in card.specs_formatted:
        lines.append(f"| {spec.name} | {spec.value} |")
    lines.append("")
    
    # Search Queries
    lines.append("## Поисковые запросы (SEO)")
    for q in card.search_queries:
        lines.append(f"- `{q}`")
    lines.append("")
    
    # Missing / Unclear Fields
    if card.missing_or_unclear_fields:
        lines.append("## Замечания контент-менеджеру (требуют уточнения)")
        for field in card.missing_or_unclear_fields:
            lines.append(f"- ⚠️ {field}")
        lines.append("")
        
    return "\n".join(lines)


def format_as_text(card: ProductCardOutput) -> str:
    """Форматирует карточку в чистый текст без спецсимволов разметки."""
    lines = [
        f"SEO-ЗАГОЛОВОК: {card.seo_title}",
        "=" * 60,
        f"КОМУ ПОДХОДИТ: {card.commercial_block.target_audience}",
        "РЕШАЕМЫЕ ЗАДАЧИ:",
        *[f"  * {task}" for task in card.commercial_block.solved_tasks],
        "=" * 60,
        "ОПИСАНИЕ:",
        card.seo_description,
        f"(Объем: {len(card.seo_description)} симв.)",
        "=" * 60,
        "ХАРАКТЕРИСТИКИ:",
        *[f"  {spec.name}: {spec.value}" for spec in card.specs_formatted],
        "=" * 60,
        "ПОИСКОВЫЕ ЗАПРОСЫ:",
        *[f"  - {q}" for q in card.search_queries],
    ]
    if card.missing_or_unclear_fields:
        lines.append("=" * 60)
        lines.append("ОТСУТСТВУЮЩИЕ / НЕПОЛНЫЕ ПОЛЯ:")
        lines.extend([f"  ! {f}" for f in card.missing_or_unclear_fields])
        
    return "\n".join(lines)


def format_as_json(card: ProductCardOutput) -> str:
    """Возвращает форматированный JSON-дамп карточки."""
    return json.dumps(card.model_dump(), ensure_ascii=False, indent=2)
