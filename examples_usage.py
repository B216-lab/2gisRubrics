"""
Расширенные примеры использования классификатора
Загрузка из файлов, обработка батчей, валидация результатов
"""

import json
import csv
import pandas as pd
from rubrics_classifier import RubricsClassifier, prepare_categories_from_dict
from pathlib import Path


# ======================= ЗАГРУЗКА ДАННЫХ =======================

def load_categories_from_csv(csv_path: str) -> list:
    """Загрузка категорий из CSV файла"""
    categories = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            categories.append({
                'id': int(row['№']),
                'name': row['Тип'],
                'description': row.get('Общее описание', '')
            })
    return categories


def load_categories_from_json(json_path: str) -> list:
    """Загрузка категорий из JSON файла"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'categories' in data:
        return data['categories']
    else:
        raise ValueError("Неподдерживаемый формат JSON")


def load_rubrics_from_file(file_path: str) -> list:
    """Загрузка рубрик из CSV или JSON"""
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path, encoding='utf-8')
        return df['rubric'].tolist() if 'rubric' in df.columns else df.iloc[:, 0].tolist()
    
    elif file_path.endswith('.json'):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) else data.get('rubrics', [])
    
    else:
        raise ValueError("Поддерживаются только CSV и JSON")


# ======================= ИНСТРУМЕНТЫ ВАЛИДАЦИИ =======================

def validate_classification_quality(results: list, min_confidence: float = 0.5) -> dict:
    """
    Анализирует качество классификации
    
    Args:
        results: Результаты из classify_batch
        min_confidence: Минимальный уровень уверенности для успешной классификации
    
    Returns:
        Словарь со статистикой
    """
    total = len(results)
    confident = 0  # Классификация с confidence >= min_confidence
    multi_option = 0  # Рубрики с несколькими вариантами
    unclassified = 0  # Не классифицированные рубрики
    
    top_1_match = []
    
    for result in results:
        if not result['classifications']:
            unclassified += 1
        else:
            top_score = result['classifications'][0]['confidence']
            if top_score >= min_confidence:
                confident += 1
            
            if len(result['classifications']) > 1:
                multi_option += 1
            
            top_1_match.append({
                'rubric': result['rubric'],
                'category': result['classifications'][0]['category_name'],
                'confidence': top_1_match
            })
    
    return {
        'total_rubrics': total,
        'confident_classifications': confident,
        'confidence_rate': round(confident / total * 100, 2) if total > 0 else 0,
        'multi_option_cases': multi_option,
        'unclassified': unclassified,
        'unclassified_rate': round(unclassified / total * 100, 2) if total > 0 else 0,
    }


def filter_results_by_confidence(results: list, min_confidence: float = 0.6) -> dict:
    """
    Разделяет результаты на уверенные и сомнительные
    
    Args:
        results: Результаты классификации
        min_confidence: Порог уверенности
    
    Returns:
        Словарь с 'confident' и 'uncertain' списками
    """
    confident = []
    uncertain = []
    
    for result in results:
        if not result['classifications']:
            uncertain.append(result)
        elif result['classifications'][0]['confidence'] >= min_confidence:
            confident.append(result)
        else:
            uncertain.append(result)
    
    return {
        'confident': confident,
        'uncertain': uncertain,
        'summary': {
            'confident_count': len(confident),
            'uncertain_count': len(uncertain),
            'total': len(results)
        }
    }


# ======================= РАСШИРЕННЫЙ ЭКСПОРТ =======================

def export_results_with_summary(results: list, output_dir: str, 
                                min_confidence: float = 0.6) -> None:
    """
    Сохраняет результаты с разделением на уверенные/сомнительные
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Основные результаты
    classifier = RubricsClassifier()
    classifier.export_results(results, f"{output_dir}/all_classifications.csv", format='csv')
    
    # Анализ качества
    quality = validate_classification_quality(results, min_confidence)
    with open(f"{output_dir}/quality_report.json", 'w', encoding='utf-8') as f:
        json.dump(quality, f, ensure_ascii=False, indent=2)
    
    # Разделение на уверенные/сомнительные
    filtered = filter_results_by_confidence(results, min_confidence)
    
    # Уверенные классификации
    confident_df = pd.DataFrame([
        {
            'rubric': r['rubric'],
            'category': r['classifications'][0]['category_name'],
            'confidence': r['classifications'][0]['confidence']
        }
        for r in filtered['confident']
    ])
    confident_df.to_csv(f"{output_dir}/confident_classifications.csv", index=False, encoding='utf-8')
    
    # Сомнительные классификации (требуют ручной проверки)
    uncertain_data = []
    for r in filtered['uncertain']:
        row = {'rubric': r['rubric']}
        if r['classifications']:
            for i, clf in enumerate(r['classifications'][:3], 1):
                row[f'option_{i}'] = clf['category_name']
                row[f'confidence_{i}'] = clf['confidence']
        else:
            row['option_1'] = 'Не классифицирована'
            row['confidence_1'] = 0
        uncertain_df = pd.DataFrame([row])
        uncertain_data.append(row)
    
    uncertain_df = pd.DataFrame(uncertain_data)
    uncertain_df.to_csv(f"{output_dir}/uncertain_classifications.csv", index=False, encoding='utf-8')
    
    print(f"\n✓ Результаты сохранены в {output_dir}/")
    print(f"  - all_classifications.csv (полный список)")
    print(f"  - confident_classifications.csv ({len(filtered['confident'])} записей)")
    print(f"  - uncertain_classifications.csv ({len(filtered['uncertain'])} записей для проверки)")
    print(f"  - quality_report.json (статистика)")


# ======================= ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ =======================

def example_1_basic_usage():
    """Пример 1: Базовое использование"""
    print("="*80)
    print("ПРИМЕР 1: Базовое использование")
    print("="*80)
    
    categories = [
        {'id': 1, 'name': 'Жильё', 'description': 'Жилой комплекс; частные дома'},
        {'id': 11, 'name': 'Общепит', 'description': 'Кафе, ресторан; кофейня; столовая'},
        {'id': 13, 'name': 'Спорт', 'description': 'Спортивные комплекс, тренажерный зал, бассейн'},
        {'id': 5, 'name': 'Медицина', 'description': 'Больница, стоматология, поликлиника'},
    ]
    
    test_rubrics = [
        'Рестораны',
        'Кафе',
        'Больницы',
        'Тренажерные залы',
        'Жилые комплексы',
    ]
    
    classifier = RubricsClassifier()
    classifier.load_categories(categories)
    results = classifier.classify_batch(test_rubrics, top_n=2)
    
    # Вывод
    for result in results:
        print(f"\n{result['rubric']}:")
        for clf in result['classifications']:
            print(f"  → {clf['category_name']:30} ({clf['confidence']:.1%})")


def example_2_from_csv_files():
    """Пример 2: Загрузка из CSV файлов"""
    print("\n" + "="*80)
    print("ПРИМЕР 2: Загрузка из CSV файлов")
    print("="*80)
    
    # Создаем пример CSV с категориями
    categories_csv = "categories.csv"
    rubrics_csv = "rubrics.csv"
    
    # Проверяем наличие файлов (если их нет, пропускаем)
    if Path(categories_csv).exists() and Path(rubrics_csv).exists():
        categories = load_categories_from_csv(categories_csv)
        rubrics = load_rubrics_from_file(rubrics_csv)
        
        classifier = RubricsClassifier()
        classifier.load_categories(categories)
        results = classifier.classify_batch(rubrics[:20], top_n=3)  # Первые 20 для теста
        
        export_results_with_summary(results, 'classification_results', min_confidence=0.6)
    else:
        print(f"Файлы {categories_csv} или {rubrics_csv} не найдены")
        print("Скопируйте свои данные в эти файлы и повторите попытку")


def example_3_quality_analysis():
    """Пример 3: Анализ качества классификации"""
    print("\n" + "="*80)
    print("ПРИМЕР 3: Анализ качества классификации")
    print("="*80)
    
    # Пример результатов
    results = [
        {
            'rubric': 'Рестораны',
            'classifications': [
                {'category_id': 11, 'category_name': 'Общепит', 'confidence': 0.95}
            ]
        },
        {
            'rubric': 'Неизвестная рубрика XYZ',
            'classifications': [
                {'category_id': 3, 'category_name': 'Торговля', 'confidence': 0.42},
                {'category_id': 5, 'category_name': 'Медицина', 'confidence': 0.35}
            ]
        },
    ]
    
    quality = validate_classification_quality(results, min_confidence=0.6)
    
    print("\nСтатистика качества:")
    for key, value in quality.items():
        print(f"  {key}: {value}")


def example_4_incremental_classification():
    """Пример 4: Пошаговая классификация с прогрессом"""
    print("\n" + "="*80)
    print("ПРИМЕР 4: Пошаговая классификация больших объемов")
    print("="*80)
    
    categories = [
        {'id': 1, 'name': 'Жильё', 'description': 'Жилой комплекс'},
        {'id': 11, 'name': 'Общепит', 'description': 'Кафе, ресторан'},
        {'id': 13, 'name': 'Спорт', 'description': 'Спортивные комплекс'},
        {'id': 5, 'name': 'Медицина', 'description': 'Больница, поликлиника'},
    ]
    
    # Большой список рубрик (для примера повторяем)
    test_rubrics = [
        'Рестораны', 'Кафе', 'Больницы', 'Тренажерные залы', 
        'Жилые комплексы', 'Поликлиники', 'Бассейны', 'Бургерные'
    ] * 5  # 40 элементов
    
    classifier = RubricsClassifier()
    classifier.load_categories(categories)
    
    # Обработка батчами (можно обработать очень большое количество)
    batch_size = 20
    all_results = []
    
    for i in range(0, len(test_rubrics), batch_size):
        batch = test_rubrics[i:i+batch_size]
        print(f"Обработка батча {i//batch_size + 1} ({i+1}-{min(i+batch_size, len(test_rubrics))} из {len(test_rubrics)})")
        batch_results = classifier.classify_batch(batch, top_n=2)
        all_results.extend(batch_results)
    
    print(f"\nВсего обработано: {len(all_results)} рубрик")


if __name__ == "__main__":
    # Запуск примеров (раскомментируй нужные)
    
    example_1_basic_usage()
    # example_2_from_csv_files()
    example_3_quality_analysis()
    # example_4_incremental_classification()
