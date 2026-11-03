from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class ProductInput(BaseModel):
    """Схема входных данных о товаре (КИПиА)."""
    name: str = Field(..., description="Название товара")
    manufacturer: str = Field(..., description="Производитель")
    specs: Dict[str, Any] = Field(default_factory=dict, description="Технические характеристики")
    description: Optional[str] = Field(default="", description="Текстовое описание или фрагмент паспорта")

    @field_validator("name", "manufacturer")
    @classmethod
    def check_non_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Поле не может быть пустым")
        return stripped


class CommercialBlock(BaseModel):
    """Commercial-блок для менеджера по продажам."""
    target_audience: str = Field(
        ...,
        description="Кому подходит данный прибор (целевая аудитория, отрасли, предприятия)"
    )
    solved_tasks: List[str] = Field(
        ...,
        description="Ключевые прикладные задачи, которые решает прибор на объекте"
    )


class SpecItem(BaseModel):
    """Единичная техническая характеристика прибора."""
    name: str = Field(
        ...,
        description="Наименование параметра (например, 'Диапазон измерений', 'Класс точности', 'Присоединение')"
    )
    value: str = Field(
        ...,
        description="Значение параметра строго из входных данных. Если параметра нет — 'данных нет'"
    )


class ProductCardOutput(BaseModel):
    """Схема готового черновика карточки товара для B2B e-commerce."""
    seo_title: str = Field(
        ...,
        description="SEO-заголовок страницы товара, строго до 70 символов с пробелами"
    )
    seo_description: str = Field(
        ...,
        description="SEO-описание товара для B2B каталога, целевой объем 800–1200 символов"
    )
    specs_formatted: List[SpecItem] = Field(
        ...,
        description="Структурированный список характеристик строго из входных данных. Параметры без данных помечаются как 'данных нет'"
    )
    search_queries: List[str] = Field(
        ...,
        min_length=3,
        max_length=5,
        description="3–5 поисковых коммерческих/информационных запросов под B2B SEO"
    )
    commercial_block: CommercialBlock = Field(
        ...,
        description="Коммерческий блок: кому подходит и какие задачи решает"
    )
    missing_or_unclear_fields: List[str] = Field(
        default_factory=list,
        description="Список критически важных для КИПиА полей, которые отсутствуют во входных данных или требуют уточнения"
    )
