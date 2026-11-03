import json
from pathlib import Path
import streamlit as st

from app.models import ProductInput
from app.agent import generate_product_card
from app.formatter import format_as_markdown, format_as_text, format_as_json
from app.validator import validate_card_output

st.set_page_config(
    page_title="Генератор карточек КИПиА | B2B AI Assistant",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ AI-помощник для карточек товаров КИПиА")
st.caption("Автоматическое создание черновиков B2B-карточек товаров на базе Agno Framework и Structured Outputs")

# Загрузка примеров
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
examples = {}
if DATA_DIR.exists():
    for f in sorted(DATA_DIR.glob("*.json")):
        try:
            examples[f.name] = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            pass

# Боковая панель настроек
with st.sidebar:
    st.header("Настройки")
    provider = st.selectbox("LLM Провайдер", ["gemini", "openai"], index=0)
    
    st.subheader("Быстрые примеры")
    selected_example = st.selectbox(
        "Загрузить тестовый товар",
        ["(свой ввод)"] + list(examples.keys())
    )

default_json = ""
if selected_example in examples:
    default_json = json.dumps(examples[selected_example], ensure_ascii=False, indent=2)
else:
    default_json = json.dumps({
        "name": "Манометр показывающий DM 02",
        "manufacturer": "Манотомь",
        "specs": {
            "диапазон измерений": "0–1,6 МПа",
            "класс точности": "1,5",
            "присоединение": "G1/2",
            "диаметр корпуса": "100 мм"
        },
        "description": "Прибор предназначен для измерения избыточного давления неагрессивных жидких и газообразных сред."
    }, ensure_ascii=False, indent=2)

col_input, col_output = st.columns([1, 1], gap="medium")

with col_input:
    st.subheader("1. Входные данные (JSON)")
    json_input = st.text_area(
        "Вставьте JSON товара:",
        value=default_json,
        height=380
    )
    generate_btn = st.button("🚀 Сгенерировать карточку", type="primary", use_container_width=True)

with col_output:
    st.subheader("2. Результат для контент-менеджера")
    if generate_btn:
        try:
            raw_dict = json.loads(json_input)
            product = ProductInput(**raw_dict)
        except json.JSONDecodeError as e:
            st.error(f"❌ Ошибка в формате JSON: {e}")
            st.stop()
        except Exception as e:
            st.error(f"❌ Ошибка валидации данных: {e}")
            st.stop()

        with st.spinner("Генерация карточки через Agno Agent..."):
            try:
                card = generate_product_card(product, provider=provider)
                st.session_state["card"] = card
            except Exception as e:
                st.error(f"❌ Ошибка вызова LLM API: {e}")
                st.stop()

    if "card" in st.session_state:
        card = st.session_state["card"]
        val = validate_card_output(card)
        
        # Метрики соблюдения ТЗ
        title_len = len(card.seo_title)
        desc_len = len(card.seo_description)
        
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("SEO Title (до 70)", f"{title_len} симв.", delta=f"{70 - title_len} ост.")
        m_col2.metric("SEO Описание (800-1200)", f"{desc_len} симв.")
        m_col3.metric("SEO Запросов", f"{len(card.search_queries)} шт.")

        if val["warnings"]:
            for w in val["warnings"]:
                st.warning(w)

        tab_md, tab_json, tab_text = st.tabs(["Markdown", "JSON", "Текст"])

        with tab_md:
            md_content = format_as_markdown(card)
            st.markdown(md_content)
            st.download_button(
                "📥 Скачать Markdown (.md)",
                data=md_content,
                file_name="product_card.md",
                mime="text/markdown",
                use_container_width=True
            )

        with tab_json:
            json_content = format_as_json(card)
            st.code(json_content, language="json")
            st.download_button(
                "📥 Скачать JSON",
                data=json_content,
                file_name="product_card.json",
                mime="application/json",
                use_container_width=True
            )

        with tab_text:
            text_content = format_as_text(card)
            st.text_area("Готовый текст:", text_content, height=350)
