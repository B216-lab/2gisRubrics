#!/usr/bin/env python3
"""
ИНТЕРАКТИВНОЕ МЕНЮ для классификации

Можешь:
- Загружать разные файлы (TXT, CSV, JSON)
- Проверять результаты онлайн
- Настраивать параметры классификации
- Экспортировать результаты в разные форматы
"""

from rubrics_classifier import RubricsClassifier
import pandas as pd
import json
import sys
from pathlib import Path

class RubricsApp:
    def __init__(self):
        self.classifier = None
        self.categories = None
        self.results = None
    
    def load_categories(self):
        """Загрузка категорий из файла"""
        print("\n" + "="*80)
        print("ЗАГРУЗКА КАТЕГОРИЙ")
        print("="*80)
        
        file_path = input("\nПуть к файлу категорий (CSV/JSON): ").strip()
        
        if not Path(file_path).exists():
            print(f"❌ Файл {file_path} не найден")
            return False
        
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8')
                self.categories = [
                    {
                        'id': row['№'],
                        'name': row['Тип'],
                        'description': row['Общее описание']
                    }
                    for _, row in df.iterrows()
                ]
            elif file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.categories = json.load(f)
            else:
                print("❌ Поддерживаются только CSV и JSON")
                return False
            
            print(f"✓ Загружено {len(self.categories)} категорий")
            
            # Инициализируем классификатор
            print("\nИнициализирую классификатор...")
            self.classifier = RubricsClassifier()
            self.classifier.load_categories(self.categories)
            print("✓ Классификатор готов")
            
            return True
        
        except Exception as e:
            print(f"❌ Ошибка при загрузке: {e}")
            return False
    
    def load_rubrics(self):
        """Загрузка рубрик из файла"""
        if not self.classifier:
            print("❌ Сначала загрузи категории!")
            return False
        
        print("\n" + "="*80)
        print("ЗАГРУЗКА РУБРИК")
        print("="*80)
        
        file_path = input("\nПуть к файлу с рубриками (TXT/CSV/JSON): ").strip()
        
        if not Path(file_path).exists():
            print(f"❌ Файл {file_path} не найден")
            return False
        
        try:
            if file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    rubrics = [line.strip() for line in f if line.strip()]
            elif file_path.endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8')
                # Берём первый столбец
                rubrics = df.iloc[:, 0].tolist()
            elif file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                rubrics = data if isinstance(data, list) else data.get('rubrics', [])
            else:
                print("❌ Поддерживаются только TXT, CSV и JSON")
                return False
            
            print(f"✓ Загружено {len(rubrics)} рубрик")
            
            # Классифицируем
            top_n = input("\nСколько топ-категорий выводить? (1-5, по умолчанию 3): ").strip() or "3"
            try:
                top_n = int(top_n)
                if top_n < 1 or top_n > 5:
                    top_n = 3
            except:
                top_n = 3
            
            print(f"\nКлассифицирую {len(rubrics)} рубрик...")
            self.results = self.classifier.classify_batch(rubrics, top_n=top_n)
            print(f"✓ Классификация завершена")
            
            return True
        
        except Exception as e:
            print(f"❌ Ошибка при загрузке: {e}")
            return False
    
    def classify_single(self):
        """Классификация одной рубрики вручную"""
        if not self.classifier:
            print("❌ Сначала загрузи категории!")
            return
        
        print("\n" + "="*80)
        print("КЛАССИФИКАЦИЯ ОДНОЙ РУБРИКИ")
        print("="*80)
        
        rubric = input("\nВведи название рубрики: ").strip()
        if not rubric:
            return
        
        results = self.classifier.classify_rubric(rubric, top_n=5)
        
        print(f"\n{rubric}:")
        print("-" * 80)
        for cat_id, cat_name, confidence in results:
            bar_filled = int(confidence * 20)
            bar = '█' * bar_filled + '░' * (20 - bar_filled)
            percentage = f"{confidence*100:5.1f}%"
            print(f"  [{bar}] {cat_name:45} {percentage}")
    
    def show_results(self):
        """Показать результаты классификации"""
        if not self.results:
            print("❌ Сначала классифицируй рубрики!")
            return
        
        print("\n" + "="*80)
        print("РЕЗУЛЬТАТЫ КЛАССИФИКАЦИИ")
        print("="*80)
        
        count = input("\nСколько первых результатов показать? (по умолчанию 10): ").strip() or "10"
        try:
            count = int(count)
        except:
            count = 10
        
        for result in self.results[:count]:
            print(f"\n{result['rubric']}")
            print("-" * 80)
            for clf in result['classifications']:
                confidence = clf['confidence']
                bar_filled = int(confidence * 20)
                bar = '█' * bar_filled + '░' * (20 - bar_filled)
                percentage = f"{confidence*100:5.1f}%"
                print(f"  [{bar}] {clf['category_name']:45} {percentage}")
    
    def export_results(self):
        """Экспорт результатов"""
        if not self.results:
            print("❌ Нет результатов для экспорта!")
            return
        
        print("\n" + "="*80)
        print("ЭКСПОРТ РЕЗУЛЬТАТОВ")
        print("="*80)
        
        output_file = input("\nПуть для сохранения (например, results.csv): ").strip()
        if not output_file:
            return
        
        # Определяем формат по расширению
        if output_file.endswith('.csv'):
            format_type = 'csv'
        elif output_file.endswith('.json'):
            format_type = 'json'
        elif output_file.endswith('.xlsx'):
            format_type = 'xlsx'
        else:
            format_type = input("Формат (csv/json/xlsx): ").strip().lower() or 'csv'
        
        try:
            self.classifier.export_results(self.results, output_file, format=format_type)
            print(f"✓ Результаты сохранены в {output_file}")
        except Exception as e:
            print(f"❌ Ошибка при сохранении: {e}")
    
    def show_stats(self):
        """Показать статистику"""
        if not self.results:
            print("❌ Нет результатов для анализа!")
            return
        
        print("\n" + "="*80)
        print("СТАТИСТИКА")
        print("="*80)
        
        total = len(self.results)
        confident = sum(1 for r in self.results if r['classifications'] and r['classifications'][0]['confidence'] >= 0.7)
        unclassified = sum(1 for r in self.results if not r['classifications'])
        
        print(f"\nВсего рубрик: {total}")
        print(f"Уверенно классифицировано (>70%): {confident} ({confident/total*100:.1f}%)")
        print(f"Не классифицировано: {unclassified} ({unclassified/total*100:.1f}%)")
        
        # Топ-5 категорий
        category_counts = {}
        for result in self.results:
            if result['classifications']:
                cat_name = result['classifications'][0]['category_name']
                category_counts[cat_name] = category_counts.get(cat_name, 0) + 1
        
        print("\nТоп-5 наиболее частых категорий:")
        for cat_name, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            percentage = count / total * 100
            print(f"  {cat_name:45} {count:3} ({percentage:5.1f}%)")
    
    def run(self):
        """Главное меню"""
        print("\n" + "="*80)
        print("СИСТЕМА КЛАССИФИКАЦИИ РУБРИК 2ГИС")
        print("="*80)
        print("\nИнтерактивное меню для классификации рубрик")
        print("Используй файлы любых форматов (TXT, CSV, JSON)")
        
        while True:
            print("\n" + "="*80)
            print("ВЫБЕРИ ДЕЙСТВИЕ:")
            print("="*80)
            print("1. Загрузить категории")
            print("2. Загрузить и классифицировать рубрики")
            print("3. Классифицировать одну рубрику вручную")
            print("4. Показать результаты")
            print("5. Статистика результатов")
            print("6. Экспортировать результаты")
            print("7. Выход")
            
            choice = input("\nВведи номер (1-7): ").strip()
            
            if choice == '1':
                self.load_categories()
            elif choice == '2':
                self.load_rubrics()
            elif choice == '3':
                self.classify_single()
            elif choice == '4':
                self.show_results()
            elif choice == '5':
                self.show_stats()
            elif choice == '6':
                self.export_results()
            elif choice == '7':
                print("\nДо свидания! 👋")
                break
            else:
                print("❌ Неверный выбор")

if __name__ == "__main__":
    app = RubricsApp()
    app.run()
