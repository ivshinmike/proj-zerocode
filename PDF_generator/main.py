import json
import os
import platform
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
from weasyprint import HTML, CSS
from jinja2 import Template


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"
FONTS_DIR = BASE_DIR / "fonts"


def ensure_directories() -> None:
    """
    Ensure that required directories exist.
    """
    for d in (DATA_DIR, TEMPLATES_DIR, OUTPUT_DIR, FONTS_DIR):
        d.mkdir(parents=True, exist_ok=True)


def list_data_files() -> List[Path]:
    """
    List all CSV and JSON files in the data directory.
    """
    files: List[Path] = []
    if DATA_DIR.exists():
        files.extend(sorted(DATA_DIR.glob("*.csv")))
        files.extend(sorted(DATA_DIR.glob("*.json")))
    return files


def list_template_files() -> List[Path]:
    """
    List all HTML templates in the templates directory.
    """
    files: List[Path] = []
    if TEMPLATES_DIR.exists():
        files.extend(sorted(TEMPLATES_DIR.glob("*.html")))
        files.extend(sorted(TEMPLATES_DIR.glob("*.htm")))
    return files


def print_menu(title: str, options: List[str]) -> None:
    """
    Print a numbered menu to the console.
    """
    print(f"\n=== {title} ===")
    for idx, opt in enumerate(options, start=1):
        print(f"{idx}. {opt}")


def choose_index(count: int, prompt: str) -> int:
    """
    Ask user to choose an index from 1..count.
    """
    while True:
        raw = input(f"{prompt} (1-{count}): ").strip()
        if not raw.isdigit():
            print("Пожалуйста, введите число.")
            continue
        idx = int(raw)
        if 1 <= idx <= count:
            return idx - 1
        print("Неверный выбор, попробуйте снова.")


def load_records_from_csv(path: Path) -> List[Dict[str, Any]]:
    df = pd.read_csv(path)
    return df.to_dict(orient="records")


def load_records_from_json(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Допускаем несколько распространённых структур
    if isinstance(data, list):
        records = data
    elif isinstance(data, dict):
        if "invoices" in data and isinstance(data["invoices"], list):
            records = data["invoices"]
        else:
            # Один объект - делаем из него список
            records = [data]
    else:
        raise ValueError("Неизвестный формат JSON данных.")

    # Убедимся, что каждый элемент - словарь
    norm_records: List[Dict[str, Any]] = []
    for item in records:
        if isinstance(item, dict):
            norm_records.append(item)
        else:
            norm_records.append({"value": item})
    return norm_records


def detect_invoice_column(records: List[Dict[str, Any]]) -> Optional[str]:
    """
    Попробовать угадать колонку с invoice id.
    """
    if not records:
        return None

    candidate_keys = [
        "invoice_id",
        "invoiceId",
        "invoice",
        "invoice_no",
        "invoice_number",
        "id",
    ]

    keys = set().union(*(r.keys() for r in records))
    for key in candidate_keys:
        if key in keys:
            return key
    return None


def choose_invoice_column(records: List[Dict[str, Any]]) -> str:
    """
    Определить колонку для invoice id, спрашивая пользователя при необходимости.
    """
    auto = detect_invoice_column(records)
    if auto:
        return auto

    # Попросим пользователя выбрать
    if not records:
        raise ValueError("Нет записей в файле данных.")

    all_keys = sorted(set().union(*(r.keys() for r in records)))
    if not all_keys:
        raise ValueError("В данных нет полей для выбора invoice id.")

    print_menu("Выберите поле, содержащее invoice id", all_keys)
    idx = choose_index(len(all_keys), "Ваш выбор")
    return all_keys[idx]


def list_invoices(records: List[Dict[str, Any]], invoice_key: str) -> List[Any]:
    """
    Вернуть список уникальных invoice id в порядке появления.
    """
    seen = set()
    result = []
    for rec in records:
        value = rec.get(invoice_key)
        if value is None:
            continue
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def open_pdf(path: Path) -> None:
    """
    Открыть PDF в системной программе.
    Работает на Windows, macOS и большинстве Linux-дистрибутивов.
    """
    try:
        system = platform.system().lower()
        if system.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif system == "darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
    except Exception as e:
        print(f"Не удалось автоматически открыть PDF: {e}")


def build_font_css() -> Optional[CSS]:
    """
    Построить CSS с подключением кириллического шрифта, если он есть.
    Ожидается файл fonts/DejaVuSans.ttf или fonts/Roboto-Regular.ttf.
    """
    font_files = [
        FONTS_DIR / "DejaVuSans.ttf",
        FONTS_DIR / "Roboto-Regular.ttf",
    ]

    font_path = None
    for f in font_files:
        if f.exists():
            font_path = f
            break

    if not font_path:
        print(
            "Внимание: шрифт для кириллицы не найден в директории 'fonts'. "
            "Создайте папку 'fonts' и положите туда, например, 'DejaVuSans.ttf' "
            "или 'Roboto-Regular.ttf'."
        )
        return None

    # WeasyPrint ожидает file:// URL; на Windows нужно заменить backslash на слеш
    font_url = font_path.as_uri()
    css_string = f"""
@font-face {{
    font-family: "PDFFont";
    src: url("{font_url}") format("truetype");
}}
body {{
    font-family: "PDFFont", sans-serif;
}}
"""
    return CSS(string=css_string)


def render_template(template_path: Path, context: Dict[str, Any]) -> str:
    html_text = template_path.read_text(encoding="utf-8")
    template = Template(html_text)
    return template.render(**context)


def generate_pdf(html_content: str, output_path: Path) -> None:
    stylesheets: List[CSS] = []
    font_css = build_font_css()
    if font_css:
        stylesheets.append(font_css)

    HTML(string=html_content, base_url=str(TEMPLATES_DIR)).write_pdf(
        str(output_path),
        stylesheets=stylesheets or None,
    )


def main() -> None:
    ensure_directories()

    print("==== Генератор PDF чеков ====")
    print(f"Директория данных:    {DATA_DIR}")
    print(f"Директория шаблонов:  {TEMPLATES_DIR}")
    print(f"Директория вывода:    {OUTPUT_DIR}")

    data_files = list_data_files()
    template_files = list_template_files()

    if not data_files:
        print("\nНет файлов данных (CSV/JSON) в директории 'data'.")
        return
    if not template_files:
        print("\nНет HTML-шаблонов в директории 'templates'.")
        return

    # Меню выбора файла данных
    data_options = [f.name for f in data_files]
    print_menu("Доступные файлы с данными", data_options)
    data_idx = choose_index(len(data_files), "Выберите файл данных")
    data_file = data_files[data_idx]

    # Меню выбора шаблона
    template_options = [f.name for f in template_files]
    print_menu("Доступные HTML-шаблоны", template_options)
    template_idx = choose_index(len(template_files), "Выберите HTML-шаблон")
    template_file = template_files[template_idx]

    # Читаем данные
    print(f"\nЧитаю данные из: {data_file.name}")
    if data_file.suffix.lower() == ".csv":
        records = load_records_from_csv(data_file)
    elif data_file.suffix.lower() == ".json":
        records = load_records_from_json(data_file)
    else:
        print("Неподдерживаемый формат файла данных.")
        return

    if not records:
        print("Файл данных не содержит записей.")
        return

    # Определяем колонку с invoice id
    invoice_key = choose_invoice_column(records)
    invoices = list_invoices(records, invoice_key)
    if not invoices:
        print(f"Не удалось найти ни одного значения '{invoice_key}' в данных.")
        return

    # Меню выбора конкретного invoice
    invoice_options = [str(inv) for inv in invoices]
    print_menu(f"Доступные чеки (по полю '{invoice_key}')", invoice_options)
    invoice_idx = choose_index(len(invoices), "Выберите invoice id")
    chosen_invoice = invoices[invoice_idx]

    # Ищем запись по выбранному invoice
    record = next((r for r in records if r.get(invoice_key) == chosen_invoice), None)
    if not record:
        print("Не удалось найти запись для выбранного invoice.")
        return

    # Рендерим HTML
    print(f"\nИспользую шаблон: {template_file.name}")
    html_content = render_template(template_file, record)

    # Генерируем и открываем PDF
    safe_invoice = str(chosen_invoice).replace(os.sep, "_")
    output_path = OUTPUT_DIR / f"invoice_{safe_invoice}.pdf"
    print(f"Генерирую PDF: {output_path}")
    generate_pdf(html_content, output_path)
    print(f"PDF успешно сохранён: {output_path}")

    open_pdf(output_path)


if __name__ == "__main__":
    main()


