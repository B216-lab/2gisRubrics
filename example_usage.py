# example_usage.py
"""
Примеры использования Classification System Pro
"""

from classifier import CompanyClassifier
from data_processor import DataProcessor
import pandas as pd

# ============================================================================
# ПРИМЕР 1: Простая классификация одной фирмы
# ============================================================================
print("=" * 70)
print("ПРИМЕР 1: Классификация одной фирмы")
print("=" * 70)

classifier = CompanyClassifier()

company = {
    'name': 'ООО ЛЮКС МОНТАЖ',
    'description': 'производственная компания',
    'rubrics': 'Металлоизделия; Светопрозрачные конструкции; Интерьерные лестницы; Кованые изделия; Сварочные работы',
    'address': '1-й Ленинский квартал, 1'
}

result = classifier.classify_company(company)
print(f"\nФирма: {result['company_name']}")
print(f"Финальная категория: {result['final_category']}")
print(f"Уверенность: {result['final_confidence']:.1%}")
print(f"Топ-3 вариантов:")
for cat, conf in result['top_3']:
    print(f"  - {cat}: {conf:.1%}")

# ============================================================================
# ПРИМЕР 2: Добавление правила обучения
# ============================================================================
print("\n" + "=" * 70)
print("ПРИМЕР 2: Добавление правила обучения")
print("=" * 70)

# Добавляем правило: если видим "ЗАГС" - классифицировать как "ЗАГС"
classifier.classifier.add_training_rule(
    keyword="ЗАГС",
    category="ЗАГС",
    priority=90
)
print("\n✓ Правило добавлено: 'ЗАГС' → 'ЗАГС' (приоритет: 90)")

# Проверяем результат
company2 = {
    'name': 'ЗАГСы',
    'description': 'орган записи актов гражданского состояния',
    'rubrics': 'ЗАГС',
    'address': 'ул. Ленина, 5'
}

result2 = classifier.classify_company(company2)
print(f"\nФирма: {result2['company_name']}")
print(f"Финальная категория: {result2['final_category']}")
print(f"Уверенность: {result2['final_confidence']:.1%} (заметьте приоритет!)")

# ============================================================================
# ПРИМЕР 3: Пакетная обработка CSV файла
# ============================================================================
print("\n" + "=" * 70)
print("ПРИМЕР 3: Обработка CSV файла из 2GIS")
print("=" * 70)

processor = DataProcessor()

# Загрузить компании
# processor.load_companies('data/companies.csv')

# Классифицировать
# processor.classify_companies()

# Сохранить результаты
# processor.save_classified('output/result.csv')

# Генерировать отчет
# report = processor.generate_report('output/report.json')

print("""
Для обработки реального файла раскомментируйте строки выше
или используйте командную строку:

    python main.py --input data/companies.csv --output output/result.csv
""")

# ============================================================================
# ПРИМЕР 4: Работа с низкой уверенностью и корректировкой
# ============================================================================
print("\n" + "=" * 70)
print("ПРИМЕР 4: Корректировка низкоуверенных классификаций")
print("=" * 70)

# Классифицируем проблемную рубрику
problem_company = {
    'name': 'ГИБДД',
    'description': 'государственная инспекция безопасности дорожного движения',
    'rubrics': 'ГИБДД, Полиция',
    'address': 'ул. Октябрьская, 10'
}

result3 = classifier.classify_company(problem_company)
print(f"\nПроблемная классификация:")
print(f"Фирма: {result3['company_name']}")
print(f"Классифицировано как: {result3['final_category']}")
print(f"Уверенность: {result3['final_confidence']:.1%}")

# Если это неправильно, добавляем корректировку
correct_category = "Отдел полиции"
classifier.add_correction(problem_company['name'], correct_category, priority=95)
print(f"\n✓ Добавлена корректировка: '{problem_company['name']}' → '{correct_category}'")

# Теперь повторно классифицируем - результат улучшится!
result3_corrected = classifier.classify_company(problem_company)
print(f"\nПосле корректировки:")
print(f"Классифицировано как: {result3_corrected['final_category']}")
print(f"Уверенность: {result3_corrected['final_confidence']:.1%}")

# ============================================================================
# ПРИМЕР 5: Просмотр всех активных правил обучения
# ============================================================================
print("\n" + "=" * 70)
print("ПРИМЕР 5: Активные правила обучения")
print("=" * 70)

rules = classifier.classifier.training_rules.get('rules', [])
print(f"\nВсего правил: {len(rules)}\n")
for i, rule in enumerate(rules, 1):
    print(f"{i}. '{rule['keyword']}' → {rule['category']} (приоритет: {rule['priority']})")

# ============================================================================
# ПРИМЕР 6: Экспорт корректировок
# ============================================================================
print("\n" + "=" * 70)
print("ПРИМЕР 6: Экспорт истории корректировок")
print("=" * 70)

classifier.export_corrections('output/my_corrections.json')
print("✓ История корректировок сохранена в output/my_corrections.json")

# ============================================================================
# ПРИМЕР 7: Использование с интеграцией в другие системы
# ============================================================================
print("\n" + "=" * 70)
print("ПРИМЕР 7: API для интеграции")
print("=" * 70)

def classify_companies_batch(companies_list):
    """
    Функция для пакетной классификации
    
    Args:
        companies_list: Список словарей с компаниями
        
    Returns:
        Список результатов классификации
    """
    results = []
    for company in companies_list:
        result = classifier.classify_company(company)
        results.append(result)
    return results

# Пример использования
test_companies = [
    {
        'name': 'Аптека "Здоровье"',
        'description': 'сеть аптек',
        'rubrics': 'Лекарства, БАД, Медицинские товары',
        'address': 'ул. Советская, 15'
    },
    {
        'name': 'Детский сад №5',
        'description': 'дошкольное образовательное учреждение',
        'rubrics': 'Детский сад, Образование',
        'address': 'ул. Садовая, 20'
    }
]

batch_results = classify_companies_batch(test_companies)

print("\nРезультаты пакетной классификации:")
for result in batch_results:
    print(f"\n{result['company_name']}")
    print(f"  → {result['final_category']} ({result['final_confidence']:.1%})")

print("\n" + "=" * 70)
print("✓ Все примеры выполнены успешно!")
print("=" * 70)
