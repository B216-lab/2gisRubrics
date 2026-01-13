# training_manager.py
"""
Управление обучением и инициализацией модели
"""

import pandas as pd
import numpy as np
from pathlib import Path
from classifier import EnhancedClassifier
from config import CATEGORIES_FILE, CLASSIFIED_OUTPUT
import json

class TrainingManager:
    """Менеджер обучения модели"""
    
    def __init__(self):
        self.classifier = EnhancedClassifier()
        self.categories_df = None
    
    def load_categories(self, filepath: str = None) -> pd.DataFrame:
        """Загрузить категории"""
        filepath = filepath or str(CATEGORIES_FILE)
        if not Path(filepath).exists():
            print(f"✗ Файл категорий не найден: {filepath}")
            return None
        
        self.categories_df = pd.read_csv(filepath, sep=';', encoding='utf-8')
        print(f"✓ Загружено {len(self.categories_df)} категорий")
        return self.categories_df
    
    def init_training_data(self, companies_file: str):
        """
        Инициализировать обучающие данные из файла компаний
        Использует известные категории для обучения модели
        """
        print("🔄 Подготовка обучающих данных...")
        
        try:
            df = pd.read_csv(companies_file, encoding='utf-8')
            print(f"✓ Загружено {len(df)} компаний")
            
            # Берем рубрики и названия как текст
            texts = []
            labels = []
            
            for idx, row in df.iterrows():
                text = f"{str(row.get('Описание', ''))} {str(row.get('Рубрики', ''))}"
                
                if text.strip():
                    texts.append(text)
                    # Используем первую рубрику как категорию
                    rubrics_str = str(row.get('Рубрики', ''))
                    if rubrics_str and rubrics_str != 'nan':
                        first_rubric = rubrics_str.split(';')[0].strip()
                        labels.append(first_rubric)
                    else:
                        labels.append('Другое')
            
            if texts and labels:
                print(f"✓ Подготовлено {len(texts)} примеров для обучения")
                return texts, labels
            else:
                print("✗ Нет данных для обучения")
                return None, None
                
        except Exception as e:
            print(f"✗ Ошибка при подготовке данных: {e}")
            return None, None
    
    def train_model(self, companies_file: str = None):
        """Обучить модель на данных компаний"""
        
        if companies_file is None:
            companies_file = 'data/companies.csv'
        
        if not Path(companies_file).exists():
            print(f"✗ Файл не найден: {companies_file}")
            return False
        
        texts, labels = self.init_training_data(companies_file)
        
        if texts is None or labels is None:
            return False
        
        print("\n🧠 Обучение модели (это может занять 1-2 минуты)...")
        
        try:
            self.classifier.train(texts, labels)
            print("✓ Модель успешно обучена и сохранена!")
            return True
        except Exception as e:
            print(f"✗ Ошибка при обучении: {e}")
            return False
    
    def quick_init(self):
        """Быстрая инициализация (загрузить кэш или обучить)"""
        print("🔄 Инициализация модели...")
        
        # Пытаемся загрузить кэш
        if self.classifier.load_model():
            print("✓ Модель загружена из кэша")
            return True
        
        # Если кэша нет, обучаем
        print("\n⚠ Кэша нет, нужно обучить модель первый раз")
        print("Это займет 1-2 минуты...\n")
        
        return self.train_model()

class RubricClassifier:
    """Отдельный классификатор только для рубрик (без фирм)"""
    
    def __init__(self):
        self.classifier = EnhancedClassifier()
        self.rubrics_data = None
    
    def load_rubrics(self, filepath: str = 'output/classified_companies.csv') -> pd.DataFrame:
        """Загрузить уникальные рубрики из классифицированных данных"""
        if not Path(filepath).exists():
            print(f"✗ Файл не найден: {filepath}")
            return None
        
        df = pd.read_csv(filepath, encoding='utf-8')
        # Извлекаем уникальные рубрики
        self.rubrics_data = df[['final_category']].drop_duplicates()
        print(f"✓ Загружено {len(self.rubrics_data)} уникальных рубрик")
        return self.rubrics_data
    
    def classify_rubric(self, rubric: str) -> dict:
        """Классифицировать одну рубрику"""
        if self.classifier.vectorizer is None:
            if not self.classifier.load_model():
                return {'error': 'Модель не загружена'}
        
        category, confidence = self.classifier.classify_text(rubric)
        top_3 = self.classifier.classify_top_n(rubric, n=3)
        
        return {
            'rubric': rubric,
            'category': category,
            'confidence': float(confidence),
            'top_3': [(cat, float(conf)) for cat, conf in top_3],
            'all_categories': self.classifier.label_encoder.classes_.tolist()
        }
    
    def classify_rubrics_batch(self, rubrics_list: list) -> list:
        """Классифицировать список рубрик"""
        results = []
        for rubric in rubrics_list:
            results.append(self.classify_rubric(rubric))
        return results
    
    def export_rubric_classification(self, rubrics_list: list, output_file: str):
        """Экспортировать классификацию рубрик"""
        results = self.classify_rubrics_batch(rubrics_list)
        
        df = pd.DataFrame(results)
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"✓ Результаты сохранены в {output_file}")
        
        return df

print("✓ Модуль training_manager.py готов")
