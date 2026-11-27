"""Create a 10-minute defense presentation and speaker notes in Russian."""

import json
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
METRICS = json.loads((REPORTS / "phiusiil_metrics.json").read_text(encoding="utf-8"))


def title(slide, text):
    slide.shapes.title.text = text


def add_text(slide, lines, size=20, left=0.8, top=1.4, width=11.7, height=5.5):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    frame = box.text_frame
    frame.word_wrap = True
    for i, line in enumerate(lines):
        p = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
        p.text = line
        p.level = 0
        p.font.name = "Aptos"
        p.font.size = Pt(size)
        p.space_after = Pt(10)


def add_footer(slide, number):
    box = slide.shapes.add_textbox(Inches(12.0), Inches(7.1), Inches(0.7), Inches(0.25))
    p = box.text_frame.paragraphs[0]
    p.text = str(number)
    p.font.size = Pt(9)
    p.alignment = PP_ALIGN.RIGHT


def main():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "Обнаружение фишинговых сайтов по признакам URL"
    slide.placeholders[1].text = (
        "Командный проект по «Основы ИИ в кибербезопасности»\n"
        "Команда: Абдуллаев Рустам, Ахметов Омар, Нұрмолда Нұрмұхаммед, Хан Дмитрий"
    )

    slides = [
        ("Постановка задачи", [
            "Цель: классифицировать URL как фишинг или легитимный ресурс",
            "Логика работы: данные → признаки → модель → оценка → объяснение",
            "Целевая роль: дополнительный score/приоритизация в SOC",
            "Безопасность: только открытый датасет и синтетические adversarial-примеры",
        ]),
        ("Датасет и предобработка", [
            "PhiUSIIL: 235 795 строк после удаления дубликатов",
            "100 945 фишинговых и 134 850 легитимных URL",
            "Открытый датасет UCI, лицензия CC BY 4.0",
            "50 числовых признаков; train 188 636, test 47 159",
            "Разделение 80/20, stratified, seed 42",
        ]),
        ("Модели и дизайн эксперимента", [
            "Baseline: Logistic Regression",
            "Классическая модель: Random Forest",
            "Нейросеть: MLP",
            "StandardScaler и одинаковая отложенная выборка",
            "Метрики: Accuracy, Precision, Recall, F1, ROC-AUC",
        ]),
        ("Результаты моделей", [
            "Random Forest: 1.000 Accuracy / Precision / Recall / F1",
            "Logistic Regression: Accuracy 0.999873, F1 0.999851 для фишинга",
            "MLP: Accuracy 0.999936, F1 0.999926 для фишинга",
            "Random Forest не допустил ошибок на отложенной выборке",
        ]),
        ("Матрица ошибок", [
            "Порядок строк/столбцов: 0 — фишинг, 1 — легитимный",
            "Random Forest: [[20189, 0], [0, 26970]]",
            "Logistic Regression: пропущено 6 фишинговых URL",
            "MLP: пропущено 3 фишинговых URL",
            "Для SOC пропуск фишинга опаснее ложного срабатывания",
        ]),
        ("Проверка утечки и URL-only-модель", [
            "Проблема: исходный датасет содержит признаки страницы и HTML",
            "URL-only модель использует 15 признаков длины, домена, HTTPS и символов",
            "Accuracy 0.996734, Precision фишинга 0.998606",
            "Recall фишинга 0.993759, F1 фишинга 0.996177",
            "Ошибок меньше идеальных метрик, но качество остаётся высоким",
        ]),
        ("Объяснимость и устойчивость", [
            "Permutation importance выделяет HTTPS, DomainLength и LetterRatio",
            "Признаки объясняют вклад модели, но не являются доказательством причинности",
            "Синтетические варианты: удаление HTTPS, IP-host, поддомены и параметры",
            "Удаление HTTPS изменило решение с легитимного на фишинг",
            "Никаких сетевых обращений к реальным доменам не выполнялось",
        ]),
        ("Применимость в SOC", [
            "Допустимо: enrichment и приоритизация URL-событий",
            "Нужны порог вероятности, ручная проверка и эскалация",
            "Не использовать как единственный механизм блокировки",
            "Мониторинг дрейфа, временная валидация и обратная связь аналитиков",
            "Ограничение: нет независимого внешнего теста",
        ]),
        ("Выводы и вклад команды", [
            "Рустам: датасет и предобработка",
            "Омар: baseline, Random Forest, MLP",
            "Нұрмұхаммед: метрики, матрицы ошибок, устойчивость и объяснимость",
            "Дмитрий: SOC-интерпретация, отчёт и демо",
            "Итог: перспективный прототип, но не готовый автономный SOC-контроль",
        ]),
    ]

    for i, (heading, lines) in enumerate(slides, start=2):
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        title(slide, heading)
        add_text(slide, lines)
        add_footer(slide, i)

    out = REPORTS / "phishing_url_defense.pptx"
    prs.save(out)

    plan = """# Пошаговый план защиты на 10 минут

## Перед защитой

1. Откройте терминал в папке `/Users/rustam/Desktop/aiproject`.
2. Откройте в VS Code: `README.md`, `reports/phishing_url_project_report.docx`, `reports/phishing_url_defense.pptx`.
3. Проверьте вкладки: папка `reports/`, папка `models/`, notebook `notebooks/01_phishing_url_detection.ipynb`.
4. Подготовьте два окна терминала: одно для воспроизведения, одно резервное.
5. Перейдите в папку репозитория:

```bash
cd /Users/rustam/Desktop/aiproject
```

## Тайминг защиты

| Время | Слайд | Что говорить и показывать |
|---|---|---|
| 0:00–1:00 | 1 | Назвать тему, цель и состав команды |
| 1:00–2:30 | 2–3 | Показать датасет, метки, класс, train/test и три модели |
| 2:30–4:30 | 4–5 | Назвать метрики и объяснить матрицу ошибок |
| 4:30–6:00 | 6 | Показать URL-only проверку и предупреждение о признаках страницы |
| 6:00–7:30 | 7 | Показать permutation importance и synthetic adversarial CSV |
| 7:30–9:00 | 8 | Объяснить применение и ограничения для SOC |
| 9:00–10:00 | 9 | Итог, вклад участников и ответы на вопросы |

## Живое демо на 1 минуту

1. Покажите отчёт метрик:

```bash
cat reports/model_metrics.csv
```

2. Запустите воспроизведение полного набора моделей:

```bash
.venv/bin/python src/evaluate_real_dataset.py
```

Не запускайте это при слабом Wi-Fi или ограниченном времени: обучение занимает заметное время. Для резервного демо покажите сохранённый JSON:

```bash
cat reports/phiusiil_metrics.json
```

3. Запустите URL-only и adversarial-проверку:

```bash
.venv/bin/python src/extended_evaluation.py
```

4. Покажите результат:

```bash
cat reports/synthetic_adversarial_results.csv
```

## Что открывать по шагам

### Шаг 1 — Репозиторий
Откройте `README.md` и быстро покажите: цель, роли, датасет, метрики и команду воспроизведения.

### Шаг 2 — Датасет
Откройте UCI-browser page или первые строки CSV в `data/raw/PhiUSIIL_Phishing_URL_Dataset.csv`. Не загружайте подозрительные домены.

### Шаг 3 — Jupyter Notebook
Откройте `notebooks/01_phishing_url_detection.ipynb`. Показать: EDA, train/test split, сравнение трех моделей, confusion matrix и объяснимость.

### Шаг 4 — Графики
Открыть:
- `reports/class_distribution.png`
- `reports/metrics_comparison.png`
- `reports/confusion_matrices.png`

### Шаг 5 — Отчёт
Открыть `reports/phishing_url_project_report.docx`. Показать постановку задачи, таблицу метрик, анализ ошибок, ограничения и SOC-применимость.

### Шаг 6 — Презентация
Открыть `reports/phishing_url_defense.pptx` и проходить строго по таймингу.

## Возможные вопросы преподавателя

### Почему Random Forest — лучший?
Потому что на отложенной выборке он дал 1.0 по основным метрикам. При этом почти идеальный результат требует проверки утечки.

### Как считались Precision и Recall?
Для положительного класса фишинга `label 0`. Accuracy считался по обоим классам.

### Какие признаки наиболее важны?
В URL-only-модели сильные признаки: IsHTTPS, DomainLength, LetterRatioInURL и количество других специальных символов. Точная важность сохранена в `url_only_audit.json`.

### Есть ли утечка?
Проведена дополнительная URL-only проверка: Accuracy 0.996734, поэтому исходные почти идеальные метрики не объясняются только HTML-признаками и данные сохраняют качество. Внешний temporal/domain split всё ещё нужен.

### Можно ли применять в реальном SOC?
Как дополнительный score для приоритизации и enrichment — да. Как автономную блокирующую систему — пока нет.

### Как протестирована устойчивость?
Тесты синтетические: удаление HTTPS перевело вариант в класс фишинга, а добавление параметров изменило confidence. Никакие реальные системы не затрагивались.

## Финальная проверка перед входом

- [ ] Репозиторий открывается.
- [ ] PDF/DOCX и PPTX сохранены.
- [ ] Метрики приведены к одному положительному классу.
- [ ] Графики открываются.
- [ ] Команда знает роли.
- [ ] CSV adversarial не содержит реальных доменов.
- [ ] Все участники могут объяснить свой вклад.
"""
    (REPORTS / "defense_plan.md").write_text(plan, encoding="utf-8")
    print(f"Created {out}")
    print("Created reports/defense_plan.md")


if __name__ == "__main__":
    main()
