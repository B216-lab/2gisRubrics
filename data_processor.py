# data_processor.py
"""Обработка данных из 2GIS формата"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List
from config import COMPANIES_FILE, CLASSIFIED_OUTPUT, REPORT_FILE
from classifier import CompanyClassifier
import json
from tqdm import tqdm

class DataProcessor:
    """Обработчик данных компаний"""
    
    def __init__(self):
        self.companies_df = None
        self.classified_df = None
        self.classifier = CompanyClassifier()
        
    def load_companies(self, filepath: str) -> pd.DataFrame:
        """Загрузить компании из CSV (формат 2GIS)"""
        print(f"📂 Загрузка компаний из {filepath}...")
        self.companies_df = pd.read_csv(filepath, encoding='utf-8')
        print(f"✓ Загружено {len(self.companies_df)} компаний")
        print(f"  Колонки: {self.companies_df.columns.tolist()}")
        return self.companies_df
    
    def classify_companies(self, load_cached_model: bool = True) -> pd.DataFrame:
        """Классифицировать все компании"""
        if self.companies_df is None:
            raise ValueError("Сначала загрузите компании")
        
        print("\n🔄 Классификация компаний...")
        
        # Загружаем кэшированную модель если она есть
        if load_cached_model:
            self.classifier.classifier.load_model()
        
        results = []
        for idx, row in tqdm(self.companies_df.iterrows(), 
                             total=len(self.companies_df),
                             desc="Классификация"):
            company_data = {
                'name': str(row.get('Наименование', '')),
                'description': str(row.get('Описание', '')),
                'rubrics': str(row.get('Рубрики', '')),
                'address': str(row.get('Адрес', '')),
                'type': str(row.get('Тип', ''))
            }
            
            result = self.classifier.classify_company(company_data)
            results.append(result)
        
        # Создаем DataFrame результатов
        self.classified_df = pd.DataFrame(results)
        print(f"✓ Классифицировано {len(self.classified_df)} компаний")
        
        return self.classified_df
    
    def save_classified(self, filepath: str = None):
        """Сохранить классифицированные данные"""
        if self.classified_df is None:
            raise ValueError("Нет классифицированных данных")
        
        filepath = filepath or str(CLASSIFIED_OUTPUT)
        self.classified_df.to_csv(filepath, index=False, encoding='utf-8')
        print(f"✓ Результаты сохранены в {filepath}")
    
    def generate_report(self, filepath: str = None) -> Dict:
        """Генерировать отчет классификации"""
        if self.classified_df is None:
            raise ValueError("Нет классифицированных данных")
        
        # Статистика
        report = {
            'total_companies': len(self.classified_df),
            'unique_categories': self.classified_df['final_category'].nunique(),
            'avg_confidence': float(self.classified_df['final_confidence'].mean()),
            'min_confidence': float(self.classified_df['final_confidence'].min()),
            'max_confidence': float(self.classified_df['final_confidence'].max()),
            'categories_distribution': self.classified_df['final_category'].value_counts().to_dict(),
            'low_confidence_items': len(self.classified_df[
                self.classified_df['final_confidence'] < 0.6
            ])
        }
        
        filepath = filepath or str(REPORT_FILE)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 Отчет статистики:")
        print(f"  Всего компаний: {report['total_companies']}")
        print(f"  Уникальных категорий: {report['unique_categories']}")
        print(f"  Средняя уверенность: {report['avg_confidence']:.2%}")
        print(f"  Низкая уверенность (<60%): {report['low_confidence_items']}")
        
        return report
    
    def export_for_2gis_parser(self, filepath: str) -> pd.DataFrame:
        """Экспортировать результаты в расширенном формате 2GIS"""
        if self.classified_df is None:
            raise ValueError("Нет классифицированных данных")
        
        # Объединяем с оригинальными данными
        merged = pd.concat([
            self.companies_df,
            self.classified_df[['final_category', 'final_confidence', 'level1_category', 'level2_category']]
        ], axis=1)
        
        merged.to_csv(filepath, index=False, encoding='utf-8')
        print(f"✓ Данные экспортированы в {filepath}")
        return merged
    
    def get_low_confidence_items(self, threshold: float = 0.6) -> pd.DataFrame:
        """Получить компании с низкой уверенностью"""
        if self.classified_df is None:
            return pd.DataFrame()
        
        return self.classified_df[self.classified_df['final_confidence'] < threshold]
    
    def apply_correction(self, company_name: str, correct_category: str):
        """Применить корректировку"""
        self.classifier.add_correction(company_name, correct_category)
        print(f"✓ Добавлено правило: '{company_name}' → '{correct_category}'")

print("✓ Модуль data_processor.py готов")
