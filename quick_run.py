#!/usr/bin/env python3
"""
БЫСТРАЯ КЛАССИФИКАЦИЯ - просто запусти и получи результаты

Используй это если у тебя есть:
- categories.csv (46 категорий с описаниями)
- rubrics.txt (рубрики из 2ГИС, одна в строке)

Результат сохраняется в results.csv
"""

from rubrics_classifier import RubricsClassifier
import pandas as pd
import sys

def main():
    try:
        print("="*80)
        print("КЛАССИФИКАЦИЯ РУБРИК 2ГИС")
        print("="*80)
        
        # 1. ЗАГРУЖАЕМ КАТЕГОРИИ из CSV
        print("\n1️⃣ Загружаю категории из categories.csv...")
        try:
            categories_df = pd.read_csv('categories.csv', encoding='utf-8')
        except FileNotFoundError:
            print("❌ Файл categories.csv не найден!")
            print("   Убедись что categories.csv находится в той же папке")
            sys.exit(1)
        
        categories = [
            {
                'id': row['№'],
                'name': row['Тип'],
                'description': row['Общее описание']
            }
            for _, row in categories_df.iterrows()
        ]
        print(f"   ✓ Загружено {len(categories)} категорий")
        
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
        print("  - categories.csv содержит столбцы: №, Тип, Общее описание")
        print("  - rubrics.txt содержит одну рубрику в каждой строке")
        print("  - Установлены зависимости: pip install sentence-transformers scikit-learn pandas")
        sys.exit(1)

if __name__ == "__main__":
    main()
