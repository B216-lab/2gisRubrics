# main_fixed.py
"""Главный файл приложения - ИСПРАВЛЕННАЯ ВЕРСИЯ"""

import sys
import argparse
from pathlib import Path
from data_processor import DataProcessor
from classifier import CompanyClassifier
from training_manager import TrainingManager, RubricClassifier
from ui import CLI
import pandas as pd
import json

def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description='Classification System Pro - Система классификации рубрик',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  # Интерактивный режим
  python main.py

  # Обучить модель (ПЕРВЫЙ РАЗ!)
  python main.py --train data/companies.csv

  # Классифицировать файл
  python main.py --input data/companies.csv --output output/result.csv

  # Добавить правило обучения
  python main.py --add-rule "ЗАГС" "ЗАГС" --priority 90

  # Генерировать отчет
  python main.py --input data/companies.csv --report output/report.json
        """
    )
    
    parser.add_argument('--train', help='Обучить модель на данных из CSV')
    parser.add_argument('--input', '-i', help='Путь к входному файлу (CSV)')
    parser.add_argument('--output', '-o', help='Путь к выходному файлу (CSV)')
    parser.add_argument('--report', '-r', help='Генерировать отчет (JSON)')
    parser.add_argument('--add-rule', nargs=2, metavar=('KEYWORD', 'CATEGORY'),
                       help='Добавить правило обучения')
    parser.add_argument('--priority', type=int, default=50, 
                       help='Приоритет правила (1-100, default: 50)')
    parser.add_argument('--classify-rubrics', help='Классифицировать рубрики из файла')
    parser.add_argument('--show-rules', action='store_true', 
                       help='Показать все правила обучения')
    parser.add_argument('--version', '-v', action='store_true', 
                       help='Показать версию')
    
    args = parser.parse_args()
    
    # Версия
    if args.version:
        print("Classification System Pro v2.0 (FIXED)")
        return
    
    # Интерактивный режим (по умолчанию)
    if not any([args.input, args.add_rule, args.show_rules, args.train, args.classify_rubrics]):
        cli = CLI()
        cli.run()
        return
    
    # Обучение модели
    if args.train:
        trainer = TrainingManager()
        if Path(args.train).exists():
            trainer.train_model(args.train)
        else:
            print(f"✗ Файл не найден: {args.train}")
        return
    
    # Пакетная обработка
    processor = DataProcessor()
    classifier = CompanyClassifier()
    
    # Добавить правило
    if args.add_rule:
        keyword, category = args.add_rule
        classifier.classifier.add_training_rule(keyword, category, args.priority)
        print(f"✓ Правило добавлено: '{keyword}' → '{category}' (приоритет: {args.priority})")
        return
    
    # Показать правила
    if args.show_rules:
        rules = classifier.classifier.training_rules.get('rules', [])
        if not rules:
            print("Нет правил обучения")
            return
        print(f"Активных правил: {len(rules)}\n")
        for i, rule in enumerate(rules, 1):
            print(f"{i}. '{rule['keyword']}' → {rule['category']} (приоритет: {rule['priority']})")
        return
    
    # Классификация рубрик
    if args.classify_rubrics:
        rubric_classifier = RubricClassifier()
        rubric_classifier.classifier.load_model()
        
        if Path(args.classify_rubrics).exists():
            df = pd.read_csv(args.classify_rubrics, encoding='utf-8')
            rubrics = df.iloc[:, 0].tolist()  # Первая колонка
            results = rubric_classifier.classify_rubrics_batch(rubrics)
            
            output_file = 'output/rubrics_classified.csv'
            pd.DataFrame(results).to_csv(output_file, index=False, encoding='utf-8')
            print(f"✓ Результаты сохранены в {output_file}")
        return
    
    # Классификация компаний
    if args.input:
        if not Path(args.input).exists():
            print(f"✗ Файл не найден: {args.input}")
            return
        
        print(f"📂 Загрузка компаний из {args.input}...")
        processor.load_companies(args.input)
        
        print("🔄 Классификация компаний...")
        processor.classify_companies()
        
        if args.output:
            processor.save_classified(args.output)
            print(f"✓ Результаты сохранены в {args.output}")
        
        if args.report:
            processor.generate_report(args.report)
            print(f"✓ Отчет сохранен в {args.report}")

if __name__ == '__main__':
    main()
