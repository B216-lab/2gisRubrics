# classifier_ИСПРАВЛЕННЫЙ_V2.py
"""
ИСПРАВЛЕННАЯ версия классификатора
✅ Исправлена ошибка: training_rules - это список, не словарь
✅ Правильная инициализация
✅ Безопасная работа с данными
"""

import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import os
from pathlib import Path

class CompanyClassifier:
    """Классификатор компаний с поддержкой правил"""
    
    def __init__(self, model_path='models'):
        self.model_path = Path(model_path)
        self.model_path.mkdir(exist_ok=True)
        
        # Инициализация компонентов
        self.vectorizer = None
        self.classifier = None
        self.label_encoder = None
        self.training_rules = []  # ИСПРАВЛЕНО: это список!
        self.categories = []
        
        # Загружаем модель если существует
        self.load_model()
    
    def load_model(self):
        """Загрузить модель из файлов"""
        try:
            vectorizer_path = self.model_path / 'vectorizer.pkl'
            classifier_path = self.model_path / 'classifier_model.pkl'
            encoder_path = self.model_path / 'label_encoder.pkl'
            
            if vectorizer_path.exists():
                with open(vectorizer_path, 'rb') as f:
                    self.vectorizer = pickle.load(f)
            
            if classifier_path.exists():
                with open(classifier_path, 'rb') as f:
                    self.classifier = pickle.load(f)
            
            if encoder_path.exists():
                with open(encoder_path, 'rb') as f:
                    self.label_encoder = pickle.load(f)
            
            # Если моделей нет, создаем новые
            if not self.vectorizer:
                self.vectorizer = TfidfVectorizer(max_features=5000, lowercase=True, stop_words='english')
            
            if not self.classifier:
                self.classifier = MultinomialNB()
            
            print("✅ Модель загружена успешно")
        
        except Exception as e:
            print(f"⚠️ Ошибка загрузки модели: {e}")
            self.vectorizer = TfidfVectorizer(max_features=5000, lowercase=True, stop_words='english')
            self.classifier = MultinomialNB()
    
    def save_model(self):
        """Сохранить модель в файлы"""
        try:
            if self.vectorizer:
                with open(self.model_path / 'vectorizer.pkl', 'wb') as f:
                    pickle.dump(self.vectorizer, f)
            
            if self.classifier:
                with open(self.model_path / 'classifier_model.pkl', 'wb') as f:
                    pickle.dump(self.classifier, f)
            
            if self.label_encoder:
                with open(self.model_path / 'label_encoder.pkl', 'wb') as f:
                    pickle.dump(self.label_encoder, f)
            
            print("✅ Модель сохранена успешно")
        
        except Exception as e:
            print(f"❌ Ошибка сохранения модели: {e}")
    
    def add_training_rule(self, keyword, category, priority=50):
        """Добавить правило классификации"""
        try:
            # ИСПРАВЛЕНО: добавляем элемент в список, не в словарь
            rule = {
                'keyword': keyword.lower(),
                'category': category,
                'priority': priority
            }
            self.training_rules.append(rule)
            print(f"✅ Правило добавлено: {keyword} -> {category}")
            return True
        
        except Exception as e:
            print(f"❌ Ошибка добавления правила: {e}")
            return False
    
    def check_rules(self, text):
        """Проверить текст по правилам"""
        try:
            text_lower = text.lower()
            matched_rules = []
            
            # ИСПРАВЛЕНО: iterate по списку правил
            for rule in self.training_rules:
                keyword = rule.get('keyword', '')
                category = rule.get('category', '')
                priority = rule.get('priority', 50)
                
                if keyword and keyword in text_lower:
                    matched_rules.append({
                        'category': category,
                        'priority': priority,
                        'keyword': keyword
                    })
            
            # Возвращаем правило с наибольшим приоритетом
            if matched_rules:
                best_rule = max(matched_rules, key=lambda x: x['priority'])
                return best_rule['category'], best_rule['priority'] / 100.0
            
            return None, None
        
        except Exception as e:
            print(f"⚠️ Ошибка проверки правил: {e}")
            return None, None
    
    def classify_text(self, text):
        """Классифицировать текст"""
        try:
            if not text or not isinstance(text, str):
                return 'Неизвестно', 0.0
            
            # ИСПРАВЛЕНО: сначала проверяем правила
            rule_category, rule_confidence = self.check_rules(text)
            
            # Если нашли правило с высоким приоритетом, используем его
            if rule_category and rule_confidence and rule_confidence > 0.7:
                return rule_category, rule_confidence
            
            # Иначе используем модель
            if not self.classifier or not self.vectorizer:
                return 'Неизвестно', 0.0
            
            try:
                # Векторизуем текст
                X = self.vectorizer.transform([text])
                
                # Получаем вероятности
                probabilities = self.classifier.predict_proba(X)[0]
                
                # Получаем классы
                classes = self.classifier.classes_
                
                # Находим класс с максимальной вероятностью
                max_idx = np.argmax(probabilities)
                predicted_class = classes[max_idx]
                predicted_prob = probabilities[max_idx]
                
                # Конвертируем в строку если нужно
                category = str(predicted_class) if predicted_class else 'Неизвестно'
                confidence = float(predicted_prob) if predicted_prob else 0.0
                
                return category, confidence
            
            except Exception as e:
                print(f"⚠️ Ошибка классификации моделью: {e}")
                return 'Неизвестно', 0.0
        
        except Exception as e:
            print(f"❌ Ошибка classify_text: {e}")
            return 'Неизвестно', 0.0
    
    def classify_top_n(self, text, n=3):
        """Классифицировать текст и вернуть топ N"""
        try:
            if not text or not isinstance(text, str):
                return [('Неизвестно', 0.0)]
            
            if not self.classifier or not self.vectorizer:
                return [('Неизвестно', 0.0)]
            
            try:
                # Векторизуем текст
                X = self.vectorizer.transform([text])
                
                # Получаем вероятности
                probabilities = self.classifier.predict_proba(X)[0]
                
                # Получаем классы
                classes = self.classifier.classes_
                
                # Создаем список (класс, вероятность)
                results = []
                for cls, prob in zip(classes, probabilities):
                    results.append((str(cls), float(prob)))
                
                # Сортируем по вероятности в убывающем порядке
                results.sort(key=lambda x: x[1], reverse=True)
                
                # Возвращаем топ N
                return results[:n] if results else [('Неизвестно', 0.0)]
            
            except Exception as e:
                print(f"⚠️ Ошибка classify_top_n: {e}")
                return [('Неизвестно', 0.0)]
        
        except Exception as e:
            print(f"❌ Ошибка classify_top_n: {e}")
            return [('Неизвестно', 0.0)]
    
    def train(self, texts, labels):
        """Обучить модель"""
        try:
            if not texts or not labels:
                print("❌ Нет данных для обучения")
                return False
            
            # Обучаем векторайзер
            X = self.vectorizer.fit_transform(texts)
            
            # Обучаем классификатор
            self.classifier.fit(X, labels)
            
            # Сохраняем уникальные категории
            self.categories = list(set(labels))
            
            # Сохраняем модель
            self.save_model()
            
            print(f"✅ Модель обучена на {len(texts)} примерах")
            return True
        
        except Exception as e:
            print(f"❌ Ошибка обучения: {e}")
            return False


# ==================== ИНТЕГРАЦИЯ ====================

class TextClassifier:
    """Главный интерфейс классификатора"""
    
    def __init__(self):
        self.classifier = CompanyClassifier()
    
    def classify_text(self, text):
        """Классифицировать текст"""
        return self.classifier.classify_text(text)
    
    def classify_top_n(self, text, n=3):
        """Классифицировать текст и вернуть топ N"""
        return self.classifier.classify_top_n(text, n=n)
    
    def add_training_rule(self, keyword, category, priority=50):
        """Добавить правило"""
        return self.classifier.add_training_rule(keyword, category, priority)


# ==================== ИСПОЛЬЗОВАНИЕ ====================

if __name__ == '__main__':
    print("🚀 Запуск классификатора V2...")
    
    classifier = CompanyClassifier()
    
    # Пример классификации
    test_text = "IT компания разработка программного обеспечения"
    category, confidence = classifier.classify_text(test_text)
    print(f"\nТекст: {test_text}")
    print(f"Категория: {category}")
    print(f"Уверенность: {confidence*100:.1f}%")
    
    # Пример добавления правила
    classifier.add_training_rule('IT', 'Информационные технологии', priority=80)
    
    # Пример топ-3
    top_3 = classifier.classify_top_n(test_text, n=3)
    print(f"\nТоп-3 категории:")
    for cat, conf in top_3:
        print(f"  - {cat}: {conf*100:.1f}%")
    
    print("\n✅ Классификатор готов к работе!")
