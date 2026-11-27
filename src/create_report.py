"""Generate the project report and visual assets as DOCX and Markdown."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.shared import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
METRICS_PATH = REPORTS / "phiusiil_metrics.json"


def add_table(document: Document, headers, rows, widths=None):
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = str(header)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        for run in cell.paragraphs[0].runs:
            run.bold = True
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            cells[i].text = str(value)
            cells[i].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    if widths:
        for row in table.rows:
            for i, width in enumerate(widths):
                row.cells[i].width = Inches(width)
    return table


def create_graphics(metadata):
    REPORTS.mkdir(exist_ok=True)
    models = metadata["models"]
    names = ["Logistic Regression", "Random Forest", "MLP"]
    keys = ["logistic_regression", "random_forest", "mlp"]

    frame = pd.DataFrame({
        "Модель": names,
        "Accuracy": [models[k]["accuracy"] for k in keys],
        "Precision": [models[k]["precision"] for k in keys],
        "Recall": [models[k]["recall"] for k in keys],
        "F1": [models[k]["f1"] for k in keys],
    })

    ax = frame.set_index("Модель")[["Accuracy", "Precision", "Recall", "F1"]].plot(
        kind="bar", figsize=(9, 5), ylim=(0.9998, 1.00001)
    )
    ax.set_title("Сравнение метрик на отложенной выборке")
    ax.set_ylabel("Значение метрики")
    ax.tick_params(axis="x", rotation=20)
    ax.legend(loc="lower left")
    plt.tight_layout()
    plt.savefig(REPORTS / "metrics_comparison.png", dpi=200)
    plt.close()

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    for ax, name, key in zip(axes, names, keys):
        cm = models[key]["confusion_matrix_labels_0_1"]
        im = ax.imshow(cm, cmap="Blues")
        ax.set_title(name)
        ax.set_xticks([0, 1], ["0 — фишинг", "1 — легитимный"])
        ax.set_yticks([0, 1], ["0 — фишинг", "1 — легитимный"])
        ax.set_xlabel("Предсказано")
        ax.set_ylabel("Истинный класс")
        for i in range(2):
            for j in range(2):
                ax.text(j, i, cm[i][j], ha="center", va="center", fontsize=11)
    fig.suptitle("Матрицы ошибок на отложенной выборке")
    fig.tight_layout()
    plt.savefig(REPORTS / "confusion_matrices.png", dpi=200)
    plt.close()

    labels = ["Фишинг (0)", "Легитимный (1)"]
    counts = [metadata["class_counts"]["0"], metadata["class_counts"]["1"]]
    plt.figure(figsize=(7, 5))
    plt.pie(counts, labels=labels, autopct="%1.1f%%", startangle=90)
    plt.title("Распределение классов в датасете")
    plt.tight_layout()
    plt.savefig(REPORTS / "class_distribution.png", dpi=200)
    plt.close()


def create_markdown(metadata):
    text = """# Отчёт по проекту

## Обнаружение фишинговых сайтов по признакам URL

### Постановка проблемы

Фишинговые URL используются для обмана пользователей и получения конфиденциальных данных. Задача проекта — построить и сравнить модели бинарной классификации, способные определять фишинг по признакам URL и связанных данных. Система рассматривается как инструмент поддержки SOC и не должна быть единственным основанием для автоматической блокировки.

### Описание данных

Использован открытый датасет PhiUSIIL Phishing URL (Website), лицензия CC BY 4.0. Источник: UCI Machine Learning Repository. Датасет содержит 235 795 наблюдений без явных дубликатов. Классы: 100 945 фишинговых URL (0) и 134 850 легитимных (1). После удаления FILENAME, URL, Domain, TLD и Title для обучения осталось 50 числовых признаков. Данные разделены 80/20 со стратификацией и random seed 42: 188 636 строк для обучения и 47 159 для проверки.

### Методы

Построены и сравнили три подхода: Logistic Regression как baseline, Random Forest и MLP. Признаки масштабированы StandardScaler. Модели обучены на одной обучающей выборке и проверены на одной отложенной выборке. Для всех моделей сохранены prediction и вероятностная оценка класса; метрики Precision и Recall рассчитаны для фишинг-класса (label 0).

### Результаты

Таблица метрик приведена ниже. Матрица ошибок записана как [[TN, FP], [FN, TP]].

| Модель | Accuracy | Precision | Recall | F1 | ROC-AUC | Матрица ошибок |
|---|---:|---:|---:|---:|---:|---|
| Logistic Regression | 0.999873 | 1.000000 | 0.999703 | 0.999851 | 1.000000 | [[20183, 6], [0, 26970]] |
| Random Forest | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | [[20189, 0], [0, 26970]] |
| MLP | 0.999936 | 1.000000 | 0.999851 | 0.999926 | 1.000000 | [[20186, 3], [0, 26970]] |

Logistic Regression пропустил 6 фишинговых наблюдений и не допустил ложных срабатываний. Random Forest дал нулевое количество ошибок. MLP пропустил 3 фишинговых наблюдения. Такие результаты требуют осторожности: они близки к идеальным и могут свидетельствовать о наличии легко разделимых признаков или утечки данных.

### Анализ ошибок

Ложные срабатывания увеличивают нагрузку SOC и могут привести к избыточной проверке легитимных ресурсов. Пропуски фишинга создают больший риск компрометации учетных данных. На отложенной выборке Logistic Regression пропустила 6 фишинговых наблюдений, MLP — 3, а Random Forest — ни одного. Конкретный анализ этих строк не выполнен, поскольку в сохранённой версии метрик отсутствуют идентификаторы ошибочных наблюдений. Для следующей итерации необходимо сохранить индексы FP/FN и сопоставить их признаки с примерами URL.

### Объяснимость

Для интерпретации решения должны использоваться permutation importance и SHAP. Важные признаки требуется сопоставлять с безопасным смыслом: длина URL и домена, количество поддоменов, IP в host, протокол HTTPS, подозрительные ключевые слова, признаки HTML и совпадение названия домена и страницы. Результаты не следует интерпретировать как доказательство злонамеренности URL, поскольку корреляция признаков не означает причинность.

### Устойчивость

На этапе 13–14 планируется тестировать синтетические изменения: добавление и удаление параметров, замена кодировки, добавление поддоменов, изменение регистра и использование IP-адреса. Изменения проводятся только на синтетических примерах и не обращаются к реальным доменам. Необходимо измерить долю изменения предсказания и изменение уверенности модели.

### Ограничения

- Почти идеальные метрики могут быть вызваны утечкой или высокой информативностью признаков страницы.
- Датасет не является чисто URL-only набором: он включает признаки HTML и текста страницы.
- Используется случайное разделение, которое может не имитировать реальное появление новых доменов во времени.
- Нет временной проверки, проверок по домену и проверки на дублирование похожих URL.
- Не проведён внешний тест на независимом датасете.
- Не настроен порог классификации для стоимости FP и FN.

### Применимость в реальном SOC

Система может использоваться как второй уровень приоритизации событий или дополнительный score в SIEM/SOAR. Она не должна использоваться как единственный механизм блокировки. Для пилота необходима настройка порога, временная валидация, обратная связь аналитиков и мониторинг дрейфа. Допустимый сценарий — low-risk triage и enrichment URL-событий; не рекомендуется без независимого тестирования принимать решения о блокировке доступных пользователям ресурсов.

### Заключение

На отложенной выборке Random Forest показал 100% по всем основным метрикам, Logistic Regression и MLP отличились менее чем на 0.001. Однако техническая применимость в SOC не подтверждена одной метрикой. Необходимо до защиты: добавить leakage audit, независимую временную выборку, анализ конкретных ошибок, SHAP/permutation importance и adversarial-тесты.

## Таблица вклада участников

| Участник | Роль | Основной вклад |
|---|---|---|
| Абдуллаев Рустам | Data engineer | Датасет, очистка данных, признаки |
| Ахметов Омар | ML engineer | baseline, Random Forest, MLP, подбор параметров |
| Нұрмолда Нұрмұхаммед | Evaluation & XAI analyst | метрики, матрицы ошибок, устойчивость, объяснимость |
| Хан Дмитрий | Security analyst / team lead | SOC-интерпретация, отчёт, презентация и контроль сроков |

### URL-only проверка утечки и устойчивости

Дополнительно обучена Random Forest только на 15 признаках URL и домена: длина URL и домена, наличие IP, длина TLD, число поддоменов, буквы и специальные символы, параметры и HTTPS. Результат: Accuracy 0.996734, Precision фишинга 0.998606, Recall 0.993759, F1 0.996177. Матрица ошибок: [[20063, 126], [28, 26942]]. Это подтверждает, что признаки самих URL сохраняют высокое качество даже без признаков HTML и страницы.

Наиболее влиятельные permutation-importance признаки: IsHTTPS, DomainLength, LetterRatioInURL и число специальных символов. Синтетические варианты показали: удаление HTTPS изменило вероятность легитимного класса с 0.9904 до вероятности фишинга в новом prediction, IP-host снизил вероятность легитимного класса до 0.7168, а добавление параметров привело к предсказанию фишинга с вероятностью легитимного класса 0.3138.
"""
    (REPORTS / "report.md").write_text(text, encoding="utf-8")


def create_docx(metadata):
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.65)
    section.bottom_margin = Inches(0.65)
    section.left_margin = Inches(0.75)
    section.right_margin = Inches(0.75)

    styles = doc.styles
    styles["Normal"].font.name = "Calibri"
    styles["Normal"].font.size = Pt(10.5)

    title = doc.add_heading("Отчёт по командному проекту", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle = doc.add_paragraph("Обнаружение фишинговых сайтов по признакам URL")
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.runs[0].bold = True

    doc.add_paragraph("Курс: «Основы ИИ в кибербезопасности»")
    doc.add_paragraph("Команда: 4 человека")
    doc.add_paragraph("Дата подготовки: 19 ноября 2026 г.")

    doc.add_heading("1. Постановка проблемы", level=1)
    doc.add_paragraph(
        "Фишинг является распространённым способом получения конфиденциальных данных пользователей. "
        "Цель проекта — обнаруживать фишинговые и легитимные URL с помощью моделей машинного обучения, "
        "оценивать качество решений и объяснять основания прогнозов. Система рассматривается как инструмент "
        "приоритизации оповещений SOC, а не единственный механизм автоматической блокировки."
    )

    doc.add_heading("2. Описание данных", level=1)
    doc.add_paragraph(
        "Использован открытый датасет PhiUSIIL Phishing URL (Website) из UCI Machine Learning Repository. "
        "Лицензия — CC BY 4.0. Датасет содержит 235 795 уникальных строк после удаления явных дубликатов. "
        "Классы распределены как 100 945 фишинговых URL (label 0) и 134 850 легитимных URL (label 1)."
    )
    add_table(doc, ["Параметр", "Значение"], [
        ["Источник", "UCI Machine Learning Repository, dataset 967"],
        ["Лицензия", "CC BY 4.0"],
        ["Размер после очистки", "235 795 строк"],
        ["Число признаков для моделей", "50 числовых"],
        ["Train", "188 636 строк"],
        ["Test", "47 159 строк"],
        ["Разделение", "80/20, stratified"],
        ["Random seed", "42"],
    ])
    doc.add_paragraph(
        "Из исходных текстовых столбцов удалены FILENAME, URL, Domain, TLD и Title. "
        "Остались числовые признаки URL, домена, страницы и структуры HTML. Поэтому датасет не является строго URL-only."
    )
    doc.add_picture(str(REPORTS / "class_distribution.png"), width=Inches(5.8))

    doc.add_heading("3. Предобработка и методы", level=1)
    doc.add_paragraph(
        "Данные проверены на пропуски и явные дубликаты. Числовые признаки масштабированы StandardScaler. "
        "Классы сохранены в исходной бинарной форме. Логистическая регрессия использована как baseline-модель, "
        "Random Forest — как классический ансамблевый метод и MLP — как нейросеть."
    )
    doc.add_paragraph(
        "Для честного сравнения разделение выполнено один раз с фиксированным seed=42. Метрики Accuracy, Precision, "
        "Recall, F1 и ROC-AUC рассчитаны на отложенной выборке. Precision и Recall рассчитаны для класса 0 (фишинг) "
        "в соответствии с исходной меткой датасета."
    )

    doc.add_heading("4. Результаты", level=1)
    rows = []
    for name, key in [("Logistic Regression", "logistic_regression"), ("Random Forest", "random_forest"), ("MLP", "mlp")]:
        m = metadata["models"][key]
        cm = m["confusion_matrix_labels_0_1"]
        rows.append([name, f'{m["accuracy"]:.6f}', f'{m["precision"]:.6f}', f'{m["recall"]:.6f}', f'{m["f1"]:.6f}', f'{m["roc_auc"]:.6f}', str(cm)])
    add_table(doc, ["Модель", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC", "Матрица ошибок"], rows, [1.35, 0.75, 0.75, 0.65, 0.65, 0.75, 1.25])
    doc.add_picture(str(REPORTS / "metrics_comparison.png"), width=Inches(6.3))
    doc.add_picture(str(REPORTS / "confusion_matrices.png"), width=Inches(6.3))

    doc.add_heading("5. Анализ ошибок", level=1)
    doc.add_paragraph(
        "Random Forest не допустил ошибок на отложенной выборке: матрица ошибок равна [[20189, 0], [0, 26970]]. "
        "Logistic Regression допустил 6 ложных срабатываний и ноль пропусков. MLP пропустил 3 фишинговых наблюдения. "
        "В этом отчёте матрица используется в порядке строк и столбцов [0=фишинг, 1=легитимный]."
    )
    doc.add_paragraph(
        "Ложные срабатывания увеличивают нагрузку SOC и могут привести к избыточной проверке легитимных ресурсов. "
        "Пропуски фишинга создают больший риск компрометации учетных данных. На отложенной выборке Logistic Regression пропустила 6 фишинговых наблюдений, MLP — 3, а Random Forest — ни одного. Конкретный анализ этих строк не выполнен, поскольку в сохранённой версии метрик отсутствуют идентификаторы ошибочных наблюдений. Для следующей итерации необходимо сохранить индексы FP/FN и сопоставить их признаки с примерами URL."
    )

    doc.add_heading("6. Объяснимость", level=1)
    doc.add_paragraph(
        "Для объяснения решения применим permutation importance и SHAP. Наиболее интерпретируемые признаки должны обсуждаться "
        "аналитиками совместно с безопасностным смыслом: длина URL и домена, число поддоменов, наличие IP-адреса, HTTPS, "
        "подозрительные ключевые слова, числовые параметры страницы, совпадение названия домена и заголовка."
    )
    doc.add_paragraph(
        "Feature importance показывает вклад признака в качество модели, но не доказывает причинную связь с фишингом. "
        "SHAP должен объяснять каждое решение отдельно, показывая признаки, которые увеличили или снизили вероятность класса."
    )

    doc.add_heading("7. Устойчивость и adversarial-тесты", level=1)
    doc.add_paragraph(
        "На следующих этапах необходимо выполнить синтетические изменения URL без обращения к реальным доменам: добавление параметров, "
        "замена регистpa, добавление поддоменов, использование IP-адреса в host и изменение HTTPS на HTTP. "
        "Для каждого варианта измеряются доля смены предсказания и изменение уверенности."
    )

    doc.add_heading("8. Ограничения", level=1)
    for item in [
        "Результаты близки к идеальным и требуют проверки утечки признаков.",
        "Датасет содержит признаки страницы и HTML, которые недоступны в момент первичного анализа URL.",
        "Использовано случайное разделение, а не временное разделение по датам сбора.",
        "Нет проверки на дублирование похожих доменов и URL между train и test.",
        "Не выполнена независимая проверка на внешнем датасете.",
        "Не настроен порог вероятности с учётом стоимости FP и FN.",
        "Не проведён анализ конкретных ошибочных строк и временного дрейфа.",
    ]:
        doc.add_paragraph(item, style="List Bullet")

    doc.add_heading("9. Применимость в реальном SOC", level=1)
    doc.add_paragraph(
        "Текущая система может применяться в качестве дополнительного score для приоритизации событий в SIEM/SOAR. "
        "Разумный пилотный сценарий — enrichment алерта и отправка URL на проверку аналитикам. Пока не подтверждена независимость "
        "тестовых данных и качество модели на только URL-признаках, автоматическая блокировка не рекомендуется."
    )
    doc.add_paragraph(
        "Для внедрения необходимы: временная валидация, порог с учётом стоимости ложных срабатываний, ручная проверка сомнительных решений, "
        "мониторинг precision/recall и дрейфа признаков, ежедневная обратная связь аналитиков и политика эскалации с высоким риском."
    )

    doc.add_heading("10. Выводы", level=1)
    doc.add_paragraph(
        "На отложенной выборке все три модели дали практически идеальные метрики. Random Forest показал нулевое число ошибок, "
        "но качество нельзя считать доказательством готовности к эксплуатации. Основной недостаток — возможная утечка и широкий набор "
        "признаков, включающий данные страницы. Для защиты проекта и реального пилота критично дополнительно проверить URL-only-модель, "
        "временную выборку, внешние данные, конкретные FP/FN, SHAP и устойчивость."
    )

    doc.add_heading("Приложение A. Таблица вклада участников", level=1)
    add_table(doc, ["Участник", "Роль", "Основной вклад"], [
        ["Абдуллаев Рустам", "Data engineer", "Подготовка датасета, очистка данных, обработка признаков"],
        ["Ахметов Омар", "ML engineer", "Baseline-модель, Random Forest, MLP, подбор параметров"],
        ["Нұрмолда Нұрмұхаммед", "Evaluation & XAI analyst", "Метрики, матрицы ошибок, устойчивость и объяснимость"],
        ["Хан Дмитрий", "Security analyst / team lead", "SOC-интерпретация, отчёт, презентация и контроль сроков"],
    ], [1.6, 1.7, 3.0])

    doc.add_heading("Приложение B. Воспроизводимость", level=1)
    doc.add_paragraph("Команда воспроизведения:")
    code = doc.add_paragraph()
    code.add_run(".venv/bin/python src/evaluate_real_dataset.py\n.venv/bin/python -m pytest -q").font.name = "Courier New"
    doc.add_paragraph("Seed: 42; test fraction: 0.20; метрики сохранены в reports/phiusiil_metrics.json.")

    doc.save(ROOT / "reports" / "phishing_url_project_report.docx")


def main():
    metadata = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    create_graphics(metadata)
    create_markdown(metadata)
    create_docx(metadata)
    print("Created reports/phishing_url_project_report.docx")
    print("Created reports/report.md")


if __name__ == "__main__":
    main()
