#!/usr/bin/env python3
"""
БЫСТРАЯ КЛАССИФИКАЦИЯ - со СМАРТ-ОБНАРУЖЕНИЕМ разделителя

АВТОМАТИЧЕСКИ ОПРЕДЕЛЯЕТ:
- Использует ли CSV запятую (,) или точку с запятой (;)
- Правильно обрабатывает кавычки в тексте
- Работает с любым кодированием

Установка зависимостей:
pip install sentence-transformers scikit-learn pandas numpy

Использование:
python quick_run_smart.py
"""

from rubrics_classifier import RubricsClassifier
import pandas as pd
import sys
from pathlib import Path

def detect_csv_separator(file_path):
    """Автоматически определяет разделитель в CSV (запятая или точка с запятой)"""
    with open(file_path, 'r', encoding='utf-8') as f:
        first_line = f.readline()
    
    # Считаем количество запятых и точек с запятой
    comma_count = first_line.count(',')
    semicolon_count = first_line.count(';')
    
    # Выбираем более частый разделитель
    if semicolon_count > comma_count:
        return ';'
    else:
        return ','

def main():
    try:
        print("="*80)
        print("КЛАССИФИКАЦИЯ РУБРИК 2ГИС (SMART VERSION)")
        print("="*80)
        
        # 1. ЗАГРУЖАЕМ КАТЕГОРИИ из CSV (с автоопределением разделителя)
        print("\n1️⃣ Загружаю категории из categories.csv...")
        try:
            categories_file = 'categories.csv'
            if not Path(categories_file).exists():
                print(f"❌ Файл {categories_file} не найден!")
                sys.exit(1)
            
            # Определяем разделитель
            separator = detect_csv_separator(categories_file)
            print(f"   Обнаружен разделитель: {repr(separator)}")
            
            # Загружаем с правильным разделителем
            categories_df = pd.read_csv(categories_file, encoding='utf-8', sep=separator)
            
            # Нормализуем названия столбцов (убираем пробелы)
            categories_df.columns = categories_df.columns.str.strip()
            
            print(f"   Найденные столбцы: {list(categories_df.columns)}")
            
            # Определяем какие столбцы использовать (они могут называться по-разному)
            id_col = None
            name_col = None
            desc_col = None
            
            # Ищем правильные столбцы
            for col in categories_df.columns:
                if col in ['№', 'N', 'ID', 'id', 'Num']:
                    id_col = col
                elif col in ['Тип', 'Type', 'Category', 'Название', 'Name']:
                    name_col = col
                elif col in ['Общее описание', 'Description', 'Desc', 'Описание']:
                    desc_col = col
            
            if not id_col:
                id_col = categories_df.columns[0]
            if not name_col:
                name_col = categories_df.columns[1]
            if not desc_col:
                desc_col = categories_df.columns[2] if len(categories_df.columns) > 2 else None
            
            print(f"   Используемые столбцы:")
            print(f"     - ID: {id_col}")
            print(f"     - Название: {name_col}")
            print(f"     - Описание: {desc_col if desc_col else 'N/A'}")
            
            # Формируем данные категорий
            categories = []
            for _, row in categories_df.iterrows():
                cat = {
                    'id': row[id_col],
                    'name': row[name_col],
                    'description': row[desc_col] if desc_col and pd.notna(row[desc_col]) else ''
                }
                categories.append(cat)
            
            print(f"   ✓ Загружено {len(categories)} категорий")
            
        except Exception as e:
            print(f"❌ Ошибка при загрузке категорий: {e}")
            print(f"\n📋 Диагностика:")
            print(f"   - Убедись что файл categories.csv находится в этой папке")
            print(f"   - Столбцы должны быть: №, Тип, Общее описание")
            print(f"   - Разделитель: , (запятая) или ; (точка с запятой)")
            print(f"   - Кодировка: UTF-8")
            sys.exit(1)
        
        # 2. ЗАГРУЖАЕМ РУБРИКИ из TXT
        print("\n2️⃣ Загружаю рубрики из rubrics.txt...")
        try:
            with open('rubrics.txt', 'r', encoding='utf-8') as f:
                rubrics = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print("❌ Файл rubrics.txt не найден!")
            print("   Убедись что rubrics.txt находится в той же папке")
            print("   (одна рубрика в строке)")
            sys.exit(1)
        
        print(f"   ✓ Загружено {len(rubrics)} рубрик")
        
        # 3. ИНИЦИАЛИЗИРУЕМ КЛАССИФИКАТОР
        print("\n3️⃣ Инициализирую классификатор...")
        classifier = RubricsClassifier()
        classifier.load_categories(categories)
        print("   ✓ Готово")
        
        # 4. КЛАССИФИЦИРУЕМ
        print(f"\n4️⃣ Классифицирую {len(rubrics)} рубрик...")
        results = classifier.classify_batch(rubrics, top_n=3)
        print("   ✓ Классификация завершена")
        
        # 5. СОХРАНЯЕМ РЕЗУЛЬТАТЫ
        output_file = 'results.csv'
        print(f"\n5️⃣ Сохраняю результаты в {output_file}...")
        classifier.export_results(results, output_file, format='csv')
        print(f"   ✓ Готово! Результаты в {output_file}")
        
        # 6. ПОКАЗЫВАЕМ ПЕРВЫЕ 10 РЕЗУЛЬТАТОВ
        print("\n" + "="*80)
        print("ПРИМЕРЫ РЕЗУЛЬТАТОВ (первые 10)")
        print("="*80)
        
        for result in results[:10]:
            print(f"\n{result['rubric']}")
            for clf in result['classifications']:
                confidence = clf['confidence']
                # Прогресс-бар (20 символов)
                bar_filled = int(confidence * 20)
                bar = '█' * bar_filled + '░' * (20 - bar_filled)
                percentage = f"{confidence*100:5.1f}%"
                print(f"  [{bar}] {clf['category_name']:45} {percentage}")
        
        print("\n" + "="*80)
        print(f"✅ УСПЕШНО! Обработано {len(results)} рубрик")
        print(f"📊 Результаты сохранены в {output_file}")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        print("\nДля справки, убедись что:")
        print("  - categories.csv содержит: №, Тип, Общее описание")
        print("  - Разделитель: запятая (,) или точка с запятой (;)")
        print("  - rubrics.txt содержит одну рубрику в каждой строке")
        print("  - Установлены зависимости: pip install sentence-transformers scikit-learn pandas")
        sys.exit(1)

if __name__ == "__main__":
    main()
