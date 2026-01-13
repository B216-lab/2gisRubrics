# batch_process.py
"""
Скрипт для пакетной обработки нескольких файлов CSV
"""

import os
import glob
from pathlib import Path
from data_processor import DataProcessor
from classifier import CompanyClassifier
import json
from datetime import datetime

def process_all_csv_files(input_dir='data', output_dir='output'):
    """
    Обработать все CSV файлы в директории
    
    Args:
        input_dir: Директория с файлами
        output_dir: Директория для результатов
    """
    
    # Создаем директорию для результатов
    Path(output_dir).mkdir(exist_ok=True)
    
    # Находим все CSV файлы в input_dir (кроме categories.csv)
    csv_files = glob.glob(f"{input_dir}/**/*.csv", recursive=True)
    csv_files = [f for f in csv_files if 'categories' not in f and 'training' not in f]
    
    if not csv_files:
        print(f"✗ CSV файлы не найдены в {input_dir}")
        return
    
    print(f"📂 Найдено {len(csv_files)} файлов для обработки\n")
    
    # Обработаем каждый файл
    processor = DataProcessor()
    all_results = []
    
    for file_path in csv_files:
        filename = Path(file_path).name
        print(f"🔄 Обработка: {filename}")
        
        try:
            # Загружаем
            processor.load_companies(file_path)
            
            # Классифицируем
            processor.classify_companies()
            
            # Сохраняем результаты
            output_file = f"{output_dir}/classified_{filename}"
            processor.save_classified(output_file)
            
            # Генерируем отчет
            report_file = f"{output_dir}/report_{filename.replace('.csv', '.json')}"
            report = processor.generate_report(report_file)
            
            all_results.append({
                'file': filename,
                'status': 'success',
                'total_companies': len(processor.classified_df),
                'avg_confidence': float(report['avg_confidence']),
                'categories': len(report['categories_distribution']),
                'output_file': output_file
            })
            
            print(f"✓ Готово: {output_file}\n")
            
        except Exception as e:
            print(f"✗ Ошибка при обработке {filename}: {e}\n")
            all_results.append({
                'file': filename,
                'status': 'error',
                'error': str(e)
            })
    
    # Сохраняем итоговый отчет
    summary = {
        'timestamp': datetime.now().isoformat(),
        'files_processed': len([r for r in all_results if r['status'] == 'success']),
        'files_failed': len([r for r in all_results if r['status'] == 'error']),
        'results': all_results
    }
    
    summary_file = f"{output_dir}/batch_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*70}")
    print(f"✓ Пакетная обработка завершена")
    print(f"  Успешно: {summary['files_processed']}")
    print(f"  Ошибок: {summary['files_failed']}")
    print(f"  Итоговый отчет: {summary_file}")
    print(f"{'='*70}")
    
    return summary

def apply_training_rules(rules_file='data/training_rules.json'):
    """
    Применить правила обучения из файла
    """
    classifier = CompanyClassifier()
    
    if not Path(rules_file).exists():
        print(f"✗ Файл не найден: {rules_file}")
        return
    
    with open(rules_file, 'r', encoding='utf-8') as f:
        rules_data = json.load(f)
    
    rules = rules_data.get('rules', [])
    print(f"📚 Применение {len(rules)} правил обучения...\n")
    
    for rule in rules:
        print(f"  → '{rule['keyword']}' → {rule['category']} (приоритет: {rule['priority']})")
    
    print(f"\n✓ Все правила загружены")
    return classifier

if __name__ == '__main__':
    import sys
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║         Пакетная обработка Classification System           ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    if len(sys.argv) > 1:
        input_dir = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else 'output'
    else:
        input_dir = 'data'
        output_dir = 'output'
    
    process_all_csv_files(input_dir, output_dir)
