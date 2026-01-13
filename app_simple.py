# app_simple.py
"""
Минимальное Flask приложение - БЕЗ шаблонов (простой API)
"""

from flask import Flask, request, jsonify
from pathlib import Path
import json
from classifier import CompanyClassifier
from training_manager import TrainingManager

app = Flask(__name__)

classifier = CompanyClassifier()
trainer = TrainingManager()

@app.route('/', methods=['GET'])
def index():
    """Главная страница - информация"""
    return jsonify({
        'name': 'Classification System Pro v2.0',
        'endpoints': {
            '/api/classify/rubric (POST)': 'Классифицировать рубрику',
            '/api/classify/company (POST)': 'Классифицировать компанию',
            '/api/train (POST)': 'Обучить модель',
            '/api/rules (GET)': 'Получить все правила',
            '/api/rules (POST)': 'Добавить правило',
            '/api/categories (GET)': 'Получить категории'
        }
    })

@app.route('/api/classify/rubric', methods=['POST'])
def classify_rubric():
    """Классифицировать рубрику"""
    data = request.get_json()
    rubric = data.get('rubric', '').strip()
    
    if not rubric:
        return jsonify({'error': 'Рубрика не указана'}), 400
    
    try:
        if classifier.classifier.vectorizer is None:
            classifier.classifier.load_model()
        
        category, confidence = classifier.classifier.classify_text(rubric)
        top_3 = classifier.classifier.classify_top_n(rubric, n=3)
        
        return jsonify({
            'rubric': rubric,
            'category': category,
            'confidence': float(confidence),
            'top_3': [(cat, float(conf)) for cat, conf in top_3]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/classify/company', methods=['POST'])
def classify_company_api():
    """Классифицировать компанию"""
    data = request.get_json()
    company = {
        'name': data.get('name', ''),
        'description': data.get('description', ''),
        'rubrics': data.get('rubrics', ''),
        'address': data.get('address', '')
    }
    
    if not company['name']:
        return jsonify({'error': 'Название не указано'}), 400
    
    try:
        if classifier.classifier.vectorizer is None:
            classifier.classifier.load_model()
        
        result = classifier.classify_company(company)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/train', methods=['POST'])
def train():
    """Обучить модель"""
    data = request.get_json()
    filepath = data.get('filepath', 'data/companies.csv')
    
    if not Path(filepath).exists():
        return jsonify({'error': f'Файл не найден: {filepath}'}), 400
    
    try:
        trainer.train_model(filepath)
        return jsonify({'status': 'success', 'message': 'Модель обучена'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rules', methods=['GET'])
def get_rules():
    """Получить все правила"""
    rules = classifier.classifier.training_rules.get('rules', [])
    return jsonify({
        'count': len(rules),
        'rules': rules
    })

@app.route('/api/rules', methods=['POST'])
def add_rule():
    """Добавить правило"""
    data = request.get_json()
    keyword = data.get('keyword', '').strip()
    category = data.get('category', '').strip()
    priority = int(data.get('priority', 50))
    
    if not keyword or not category:
        return jsonify({'error': 'Заполните все поля'}), 400
    
    try:
        classifier.classifier.add_training_rule(keyword, category, priority)
        return jsonify({'status': 'success', 'message': 'Правило добавлено'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Получить категории"""
    try:
        import pandas as pd
        df = pd.read_csv('data/categories.csv', sep=';', encoding='utf-8')
        categories = df[['№', 'Тип', 'Общее описание']].to_dict('records')
        return jsonify({
            'count': len(categories),
            'categories': categories
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Инициализируем модель
    print("🔄 Инициализация модели...")
    if classifier.classifier.load_model():
        print("✓ Модель загружена")
    else:
        print("⚠ Модель не найдена (обучите сначала)")
    
    print("\n🌐 Flask запущен на http://localhost:5000")
    print("📚 API документация на http://localhost:5000/")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
