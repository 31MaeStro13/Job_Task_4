import argparse
import json
import sys
from pathlib import Path
from pydantic import ValidationError

from app.models import ProductInput
from app.agent import generate_product_card
from app.formatter import format_as_markdown, format_as_text, format_as_json
from app.validator import validate_card_output


def main():
    parser = argparse.ArgumentParser(
        description="B2B AI Product Card Generator (Agno + Pydantic) для КИПиА"
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        type=str,
        help="Путь к входному JSON-файлу с данными прибора"
    )
    parser.add_argument(
        "--format",
        choices=["md", "text", "json"],
        default="md",
        help="Формат вывода результата (по умолчанию: md)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Путь для сохранения файла результата (опционально)"
    )
    parser.add_argument(
        "--provider",
        choices=["gemini", "openai"],
        help="Принудительный выбор провайдера LLM (gemini или openai)"
    )

    args = parser.parse_args()

    # 1. Чтение входных данных
    if args.input_file:
        file_path = Path(args.input_file)
        if not file_path.is_file():
            print(f"Ошибка: Файл '{args.input_file}' не найден.", file=sys.stderr)
            sys.exit(1)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Ошибка: Некорректный JSON в файле '{args.input_file}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Чтение из stdin, если файл не передан
        if sys.stdin.isatty():
            parser.print_help()
            sys.exit(1)
        try:
            raw_data = json.load(sys.stdin)
        except json.JSONDecodeError as e:
            print(f"Ошибка чтения stdin: Некорректный JSON: {e}", file=sys.stderr)
            sys.exit(1)

    # 2. Валидация входных данных
    try:
        product_input = ProductInput(**raw_data)
    except ValidationError as e:
        print("Ошибка валидации входных данных:", file=sys.stderr)
        for err in e.errors():
            loc = " -> ".join(str(x) for x in err["loc"])
            print(f"  - Поле '{loc}': {err['msg']}", file=sys.stderr)
        sys.exit(1)

    print(f"Обработка прибора: {product_input.name} ({product_input.manufacturer})...", file=sys.stderr)

    # 3. Генерация через Agno Agent
    try:
        card = generate_product_card(product_input, provider=args.provider)
    except Exception as e:
        print(f"Ошибка генерации карточки через LLM API: {e}", file=sys.stderr)
        sys.exit(1)

    # 4. Проверка ограничений и предупреждения
    validation = validate_card_output(card)
    if validation["warnings"]:
        print("\nПредупреждения валидатора:", file=sys.stderr)
        for w in validation["warnings"]:
            print(f"  ⚠️ {w}", file=sys.stderr)
        print("", file=sys.stderr)

    # 5. Форматирование результата
    if args.format == "md":
        result = format_as_markdown(card)
    elif args.format == "text":
        result = format_as_text(card)
    else:
        result = format_as_json(card)

    # 6. Вывод или запись в файл
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(result, encoding="utf-8")
        print(f"Результат сохранен в {args.output}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()
