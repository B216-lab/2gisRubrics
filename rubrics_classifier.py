"""
Система автоматической классификации рубрик 2ГИС по категориям
Использует семантические эмбеддинги для интеллектуального распределения

Установка зависимостей:
pip install sentence-transformers scikit-learn pandas numpy
"""

import json
import csv
from typing import List, Dict, Tuple, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from pathlib import Path


class RubricsClassifier:
    """Классификатор рубрик с использованием семантических эмбеддингов"""
    
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Инициализация классификатора
        
        Args:
            model_name: Название модели от HuggingFace (поддерживает русский язык)
        """
        print(f"Загружаю модель {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.categories = {}
        self.category_embeddings = {}
        self.rubrics = []
        print("✓ Модель загружена")
    
    def load_categories(self, categories_data: List[Dict]) -> None:
        """
        Загрузка категорий для классификации
        
        Args:
            categories_data: Список словарей с полями 'id', 'name', 'description'
                            Пример: [{'id': 1, 'name': 'Жильё', 'description': 'Жилой комплекс; частные дома'}]
        """
        print(f"\nЗагружаю {len(categories_data)} категорий...")
        
        for cat in categories_data:
            cat_id = cat.get('id', cat.get('Тип'))
            cat_name = cat.get('name', cat.get('Тип'))
            cat_desc = cat.get('description', cat.get('Общее описание', ''))
            
            # Объединяем название и описание для лучшего понимания контекста
            combined_text = f"{cat_name}. {cat_desc}"
            
            self.categories[cat_id] = {
                'name': cat_name,
                'description': cat_desc,
                'combined': combined_text
            }
        
        # Вычисляем эмбеддинги для всех категорий
        combined_texts = [cat['combined'] for cat in self.categories.values()]
        embeddings = self.model.encode(combined_texts, show_progress_bar=True)
        
        for (cat_id, cat_info), embedding in zip(self.categories.items(), embeddings):
            self.category_embeddings[cat_id] = embedding
        
        print(f"✓ {len(self.categories)} категорий готовы")
    
    def classify_rubric(self, rubric_name: str, top_n: int = 3, 
                       threshold: float = 0.0) -> List[Tuple[int, str, float]]:
        """
        Классифицирует одну рубрику по категориям
        
        Args:
            rubric_name: Название рубрики из 2ГИС
            top_n: Количество топ категорий для возврата
            threshold: Минимальный скор для включения в результат (0-1)
        
        Returns:
            Список кортежей (category_id, category_name, confidence_score)
            Отсортирован по убыванию уверенности
        """
        # Вычисляем эмбеддинг рубрики
        rubric_embedding = self.model.encode(rubric_name)
        
        # Сравниваем со всеми категориями
        scores = {}
        for cat_id, cat_embedding in self.category_embeddings.items():
            # Косинусное сходство (значение от -1 до 1, обычно 0 до 1 для текстов)
            similarity = cosine_similarity(
                [rubric_embedding], 
                [cat_embedding]
            )[0][0]
            # Нормализуем в диапазон 0-1
            similarity = (similarity + 1) / 2
            scores[cat_id] = similarity
        
        # Сортируем по убыванию и фильтруем по threshold
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        results = [
            (cat_id, self.categories[cat_id]['name'], score)
            for cat_id, score in sorted_scores[:top_n]
            if score >= threshold
        ]
        
        return results
    
    def classify_batch(self, rubrics: List[str], top_n: int = 3, 
                      threshold: float = 0.0) -> List[Dict]:
        """
        Классифицирует несколько рубрик одновременно
        
        Args:
            rubrics: Список названий рубрик
            top_n: Топ категорий для каждой рубрики
            threshold: Минимальный скор
        
        Returns:
            Список словарей с результатами классификации
        """
        print(f"\nКлассифицирую {len(rubrics)} рубрик...")
        
        # Вычисляем эмбеддинги для всех рубрик за раз (быстрее)
        rubric_embeddings = self.model.encode(rubrics, show_progress_bar=True)
        
        results = []
        for rubric, embedding in zip(rubrics, rubric_embeddings):
            # Сравниваем со всеми категориями
            scores = {}
            for cat_id, cat_embedding in self.category_embeddings.items():
                similarity = cosine_similarity([embedding], [cat_embedding])[0][0]
                similarity = (similarity + 1) / 2
                scores[cat_id] = similarity
            
            # Берём топ-N
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            
            result = {
                'rubric': rubric,
                'classifications': [
                    {
                        'category_id': cat_id,
                        'category_name': self.categories[cat_id]['name'],
                        'confidence': round(float(score), 4)
                    }
                    for cat_id, score in sorted_scores[:top_n]
                    if score >= threshold
                ]
            }
            results.append(result)
        
        print(f"✓ Классификация завершена")
        return results
    
    def export_results(self, results: List[Dict], output_path: str, 
                      format: str = 'csv') -> None:
        """
        Экспортирует результаты в файл
        
        Args:
            results: Результаты классификации из classify_batch
            output_path: Путь к файлу для сохранения
            format: Формат 'csv', 'json' или 'xlsx'
        """
        if format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
        
        elif format == 'csv':
            rows = []
            for item in results:
                rubric = item['rubric']
                if not item['classifications']:
                    rows.append({
                        'Рубрика': rubric,
                        'Категория_1': 'N/A',
                        'Уверенность_1': 0,
                        'Категория_2': '',
                        'Уверенность_2': '',
                        'Категория_3': '',
                        'Уверенность_3': ''
                    })
                else:
                    row = {'Рубрика': rubric}
                    for idx, clf in enumerate(item['classifications'], 1):
                        row[f'Категория_{idx}'] = clf['category_name']
                        row[f'Уверенность_{idx}'] = clf['confidence']
                    rows.append(row)
            
            df = pd.DataFrame(rows)
            df.to_csv(output_path, index=False, encoding='utf-8')
        
        elif format == 'xlsx':
            rows = []
            for item in results:
                rubric = item['rubric']
                if not item['classifications']:
                    rows.append({
                        'Рубрика': rubric,
                        'Категория_1': 'N/A',
                        'Уверенность_1': 0,
                        'Категория_2': '',
                        'Уверенность_2': '',
                        'Категория_3': '',
                        'Уверенность_3': ''
                    })
                else:
                    row = {'Рубрика': rubric}
                    for idx, clf in enumerate(item['classifications'], 1):
                        row[f'Категория_{idx}'] = clf['category_name']
                        row[f'Уверенность_{idx}'] = clf['confidence']
                    rows.append(row)
            
            df = pd.DataFrame(rows)
            df.to_excel(output_path, index=False, engine='openpyxl')
        
        print(f"✓ Результаты сохранены в {output_path}")


def prepare_categories_from_dict(categories_list: List[Dict]) -> List[Dict]:
    """Подготовка данных категорий в нужный формат"""
    return [
        {
            'id': item.get('№') or item.get('id'),
            'name': item.get('Тип') or item.get('name'),
            'description': item.get('Общее описание') or item.get('description', '')
        }
        for item in categories_list
    ]


# ======================= ПРИМЕР ИСПОЛЬЗОВАНИЯ =======================

if __name__ == "__main__":
    # 1. Определяем категории
    categories = [
        {'№': 1, 'Тип': 'Жильё', 'Общее описание': 'Жилой комплекс; частные дома'},
        {'№': 2, 'Тип': 'Супермаркеты, продуктовые рынки', 'Общее описание': 'Супермаркет, продуктовый рынок, аптека'},
        {'№': 3, 'Тип': 'Торговля (Не пищевая)', 'Общее описание': 'Вещи, быт-техника, обувь, цветочный магазин, хоз товары; автомагазин, ювелирный магазин'},
        {'№': 4, 'Тип': 'Торговля (мебель, стройматериалы)', 'Общее описание': 'Мебель, стройматериалы, окна'},
        {'№': 5, 'Тип': 'Медицина', 'Общее описание': 'Больница, стоматология, поликлиника; ветеринарная клиника, санаторий'},
        {'№': 11, 'Тип': 'Общепит', 'Общее описание': 'Кафе, ресторан; кофейня; столовая, пекарня'},
        {'№': 13, 'Тип': 'Спорт', 'Общее описание': 'Спортивные комплекс, спорт клуб, тренажерный зал, бассейн'},
        {'№': 15, 'Тип': 'Автосервис', 'Общее описание': 'Автосервис, автоцентр, автомойки, шиномонтаж'},
        {'№': 18, 'Тип': 'Библиотека', 'Общее описание': 'Библиотека'},
        {'№': 28, 'Тип': 'Отдел полиции', 'Общее описание': 'УВД, военкомат'},
    ]
    
    # 2. Примеры рубрик для классификации
    test_rubrics = [
        'Администрации районов / округов городской власти',
        'Бары',
        'Кафе',
        'Кофейни',
        'Рестораны',
        'Быстрое питание',
        'Библиотеки',
        'Спортивные клубы',
        'Тренажерные залы',
        'Бассейны',
        'Больницы',
        'Поликлиники',
        'Стоматологии',
        'Автомойки',
        'Шиномонтаж',
        'Парикмахерская',
        'Салон красоты',
    ]
    
    # 3. Инициализируем классификатор
    classifier = RubricsClassifier()
    
    # 4. Загружаем категории
    prepared_categories = prepare_categories_from_dict(categories)
    classifier.load_categories(prepared_categories)
    
    # 5. Классифицируем рубрики
    results = classifier.classify_batch(test_rubrics, top_n=3, threshold=0.0)
    
    # 6. Выводим результаты
    print("\n" + "="*80)
    print("РЕЗУЛЬТАТЫ КЛАССИФИКАЦИИ")
    print("="*80)
    for result in results:
        print(f"\nРубрика: {result['rubric']}")
        for clf in result['classifications']:
            confidence_pct = clf['confidence'] * 100
            bar_length = int(confidence_pct / 5)
            progress_bar = "█" * bar_length + "░" * (20 - bar_length)
            print(f"  [{progress_bar}] {clf['category_name']:45} {confidence_pct:6.2f}%")
    
    # 7. Сохраняем результаты (выбери один формат)
    classifier.export_results(results, 'results.csv', format='csv')
    # classifier.export_results(results, 'results.json', format='json')
    # classifier.export_results(results, 'results.xlsx', format='xlsx')
    
    # ---- ДОПОЛНИТЕЛЬНО: классификация отдельной рубрики ----
    print("\n" + "="*80)
    print("ПРИМЕР КЛАССИФИКАЦИИ ОДНОЙ РУБРИКИ")
    print("="*80)
    single_result = classifier.classify_rubric("Кинотеатры с 3D залом")
    print(f"\nРубрика: 'Кинотеатры с 3D залом'")
    for cat_id, cat_name, confidence in single_result:
        print(f"  {cat_name:45} {confidence:.4f} (категория #{cat_id})")
