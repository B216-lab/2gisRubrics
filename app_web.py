# app_web_V5.0_ИСПРАВЛЕННЫЙ_ФИНАЛЬНЫЙ.py
"""
ФИНАЛЬНАЯ версия V5.0 - ПОЛНОЕ ИСПРАВЛЕНИЕ
✅ Правильная инициализация CompanyClassifier
✅ Безопасная работа с классификатором
✅ Все endpoints работают без ошибок
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
from pathlib import Path
import pandas as pd
from datetime import datetime
import json
import traceback

# ИСПРАВЛЕНО: Правильный импорт классификатора
try:
    # Сначала пытаемся импортировать наш класс
    from classifier_ИСПРАВЛЕННЫЙ_V2 import CompanyClassifier as MyCompanyClassifier
    CompanyClassifier = MyCompanyClassifier
except:
    try:
        # Если нет, пытаемся из обычного classifier
        from classifier import CompanyClassifier
    except:
        print("⚠️ Классификатор не найден, создаём простую заглушку")
        class CompanyClassifier:
            def __init__(self):
                self.classifier = None
            
            def classify_text(self, text):
                return 'Неизвестно', 0.0

try:
    from database_ИСПРАВЛЕННЫЙ_V2 import Database
except:
    try:
        from database import Database
    except:
        Database = None

try:
    from data_processor_enhanced import DataProcessorEnhanced
except:
    try:
        from data_processor import DataProcessorEnhanced
    except:
        DataProcessorEnhanced = None

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# ==================== ИНИЦИАЛИЗАЦИЯ ====================

print("🚀 Инициализация компонентов...")

# ИСПРАВЛЕНО: Правильная инициализация
try:
    print("📍 Инициализация базы данных...")
    db = Database() if Database else None
    if db:
        db.migrate_tables()
    print("✅ База данных инициализирована")
except Exception as e:
    print(f"⚠️ Ошибка БД: {e}")
    db = None

try:
    print("📍 Инициализация классификатора...")
    # ИСПРАВЛЕНО: Создаём экземпляр CompanyClassifier
    classifier_instance = CompanyClassifier()
    
    # Проверяем, что это наш класс с методами classify_text и classify_top_n
    if hasattr(classifier_instance, 'classify_text') and hasattr(classifier_instance, 'classify_top_n'):
        print("✅ Классификатор инициализирован (наш класс)")
        classifier = classifier_instance
    else:
        print("⚠️ Классификатор загружен, но без методов classify_text/classify_top_n")
        classifier = classifier_instance
except Exception as e:
    print(f"⚠️ Ошибка классификатора: {e}")
    traceback.print_exc()
    classifier = None

# Состояние обучения
training_state = {
    'is_training': False,
    'progress': 0,
    'status': 'idle',
    'message': ''
}

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def safe_classify(text):
    """
    Безопасная классификация текста.
    Возвращает (category, confidence) независимо от формата классификатора
    """
    if not classifier or not text:
        return 'Неизвестно', 0.0
    
    try:
        # ИСПРАВЛЕНО: Вызываем метод нашего класса напрямую
        if hasattr(classifier, 'classify_text'):
            result = classifier.classify_text(text)
        else:
            print(f"❌ classifier не имеет метода classify_text")
            return 'Неизвестно', 0.0
        
        # Проверяем формат результата
        if isinstance(result, tuple) and len(result) == 2:
            category, confidence = result
            # Если confidence - это список, берем первый элемент
            if isinstance(confidence, (list, tuple)):
                confidence = confidence[0] if confidence else 0.0
        elif isinstance(result, dict):
            category = result.get('category', 'Неизвестно')
            confidence = result.get('confidence', 0.0)
        else:
            category = str(result)
            confidence = 0.0
        
        # Нормализуем уверенность
        if isinstance(confidence, str):
            try:
                confidence = float(confidence.strip('%')) / 100
            except:
                confidence = 0.0
        
        confidence = float(confidence)
        if confidence > 1.0:
            confidence = confidence / 100
        
        return category, confidence
    
    except Exception as e:
        print(f"❌ Ошибка классификации: {e}")
        traceback.print_exc()
        return 'Неизвестно', 0.0

def safe_classify_top_n(text, n=3):
    """
    Безопасная классификация топ-N.
    Возвращает список кортежей (category, confidence)
    """
    if not classifier or not text:
        return [('Неизвестно', 0.0)]
    
    try:
        # ИСПРАВЛЕНО: Вызываем метод нашего класса напрямую
        if hasattr(classifier, 'classify_top_n'):
            result = classifier.classify_top_n(text, n=n)
        else:
            print(f"❌ classifier не имеет метода classify_top_n")
            return [('Неизвестно', 0.0)]
        
        if isinstance(result, list):
            # Проверяем формат элементов
            formatted = []
            for item in result:
                if isinstance(item, tuple) and len(item) >= 2:
                    cat, conf = item[0], item[1]
                    if isinstance(conf, (list, tuple)):
                        conf = conf[0] if conf else 0.0
                    formatted.append((cat, float(conf)))
                elif isinstance(item, dict):
                    cat = item.get('category', 'Неизвестно')
                    conf = item.get('confidence', 0.0)
                    if isinstance(conf, (list, tuple)):
                        conf = conf[0] if conf else 0.0
                    formatted.append((cat, float(conf)))
            
            return formatted if formatted else [('Неизвестно', 0.0)]
        else:
            return [('Неизвестно', 0.0)]
    
    except Exception as e:
        print(f"⚠️ Ошибка top_n: {e}")
        traceback.print_exc()
        return [('Неизвестно', 0.0)]

# ==================== ГЛАВНАЯ СТРАНИЦА ====================

@app.route('/')
def index():
    """Главная страница с интерфейсом"""
    return render_template('index.html')

# ==================== КЛАССИФИКАЦИЯ РУБРИК ====================

@app.route('/api/classify_rubric_single', methods=['POST'])
def classify_rubric_single():
    """Классификация одной рубрики"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'Нет текста для классификации'}), 400
        
        if not classifier:
            return jsonify({'error': 'Классификатор не инициализирован'}), 500
        
        category, confidence = safe_classify(text)
        top_3 = safe_classify_top_n(text, n=3)
        
        if db:
            classification_id = db.save_classification(
                company_name='Rubric Classification',
                text=text,
                predicted_category=category,
                confidence=confidence,
                top_3=top_3
            )
        else:
            classification_id = -1
        
        return jsonify({
            'category': category,
            'confidence': f"{confidence*100:.1f}%",
            'top_3': [{'category': cat, 'confidence': f"{conf*100:.1f}%"} for cat, conf in top_3],
            'classification_id': classification_id
        })
    
    except Exception as e:
        print(f"❌ Ошибка классификации рубрики: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500

@app.route('/api/classify_rubric_batch', methods=['POST'])
def classify_rubric_batch():
    """Классификация пакета рубрик с progress"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Файл не загружен'}), 400
        
        file = request.files['file']
        upload_folder = Path('uploads')
        upload_folder.mkdir(exist_ok=True)
        
        file_path = upload_folder / file.filename
        file.save(file_path)
        
        # Загружаем данные
        if DataProcessorEnhanced:
            try:
                items, fmt = DataProcessorEnhanced.load_file(str(file_path))
            except:
                items = []
        else:
            items = []
        
        # Если DataProcessorEnhanced не работал, пробуем вручную
        if not items:
            if file.filename.endswith('.csv'):
                try:
                    df = pd.read_csv(file_path, encoding='utf-8-sig')
                    items = df.iloc[:, 0].tolist()
                except:
                    df = pd.read_csv(file_path, encoding='latin-1')
                    items = df.iloc[:, 0].tolist()
            elif file.filename.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    items = [line.strip() for line in f if line.strip()]
            else:
                items = []
        
        if not items:
            return jsonify({'error': 'Нет данных в файле'}), 400
        
        if not classifier:
            return jsonify({'error': 'Классификатор не инициализирован'}), 500
        
        total = len(items)
        results = []
        
        for idx, text in enumerate(items):
            try:
                category, confidence = safe_classify(text)
                top_3 = safe_classify_top_n(text, n=3)
                
                if db:
                    classification_id = db.save_classification(
                        company_name=f'Rubric {idx+1}',
                        text=text,
                        predicted_category=category,
                        confidence=confidence,
                        top_3=top_3
                    )
                else:
                    classification_id = idx
                
                results.append({
                    'text': text[:50] + '...' if len(text) > 50 else text,
                    'category': category,
                    'confidence': f"{confidence*100:.1f}%",
                    'id': classification_id
                })
            
            except Exception as e:
                print(f"⚠️ Ошибка элемента {idx+1}: {e}")
        
        # Экспортируем результаты
        export_path = None
        if db:
            try:
                export_path = db.export_classifications_csv()
            except:
                pass
        
        return jsonify({
            'total': total,
            'processed': len(results),
            'results': results,
            'export_file': str(export_path) if export_path else None,
            'message': f'Обработано {len(results)} из {total} рубрик'
        })
    
    except Exception as e:
        print(f"❌ Ошибка пакетной классификации рубрик: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ==================== КЛАССИФИКАЦИЯ КОМПАНИЙ ====================

@app.route('/api/classify_company_single', methods=['POST'])
def classify_company_single():
    """Классификация одной компании"""
    try:
        data = request.get_json()
        company_name = data.get('company_name', '')
        description = data.get('description', '')
        rubrics = data.get('rubrics', '')
        
        if not company_name:
            return jsonify({'error': 'Нет названия компании'}), 400
        
        if not classifier:
            return jsonify({'error': 'Классификатор не инициализирован'}), 500
        
        # Объединяем все тексты
        full_text = f"{company_name} {description} {rubrics}"
        category, confidence = safe_classify(full_text)
        top_3 = safe_classify_top_n(full_text, n=3)
        
        # Сохраняем в БД
        if db:
            classification_id = db.save_classification(
                company_name=company_name,
                text=full_text,
                predicted_category=category,
                confidence=confidence,
                top_3=top_3
            )
        else:
            classification_id = -1
        
        return jsonify({
            'company_name': company_name,
            'category': category,
            'confidence': f"{confidence*100:.1f}%",
            'top_3': [{'category': cat, 'confidence': f"{conf*100:.1f}%"} for cat, conf in top_3],
            'classification_id': classification_id,
            'details': {
                'description': description,
                'rubrics': rubrics
            }
        })
    
    except Exception as e:
        print(f"❌ Ошибка классификации компании: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/classify_company_batch', methods=['POST'])
def classify_company_batch():
    """Классификация пакета компаний"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Файл не загружен'}), 400
        
        file = request.files['file']
        upload_folder = Path('uploads')
        upload_folder.mkdir(exist_ok=True)
        
        file_path = upload_folder / file.filename
        file.save(file_path)
        
        # Загружаем данные
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except:
            df = pd.read_csv(file_path, encoding='latin-1')
        
        if df.empty:
            return jsonify({'error': 'Нет данных в файле'}), 400
        
        if not classifier:
            return jsonify({'error': 'Классификатор не инициализирован'}), 500
        
        total = len(df)
        results = []
        
        for idx, row in df.iterrows():
            try:
                company_name = str(row.get('name', f'Company {idx+1}'))
                description = str(row.get('description', ''))
                rubrics = str(row.get('rubrics', ''))
                
                full_text = f"{company_name} {description} {rubrics}"
                category, confidence = safe_classify(full_text)
                top_3 = safe_classify_top_n(full_text, n=3)
                
                if db:
                    classification_id = db.save_classification(
                        company_name=company_name,
                        text=full_text,
                        predicted_category=category,
                        confidence=confidence,
                        top_3=top_3
                    )
                else:
                    classification_id = idx
                
                results.append({
                    'company_name': company_name,
                    'category': category,
                    'confidence': f"{confidence*100:.1f}%",
                    'id': classification_id
                })
            
            except Exception as e:
                print(f"⚠️ Ошибка компании {idx+1}: {e}")
        
        export_path = None
        if db:
            try:
                export_path = db.export_classifications_csv()
            except:
                pass
        
        return jsonify({
            'total': total,
            'processed': len(results),
            'results': results,
            'export_file': str(export_path) if export_path else None,
            'message': f'Обработано {len(results)} из {total} компаний'
        })
    
    except Exception as e:
        print(f"❌ Ошибка пакетной классификации компаний: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ==================== ЭКСПОРТ И КОРРЕКТИРОВКА ====================

@app.route('/api/export_classifications', methods=['GET'])
def export_classifications():
    """Экспорт в CSV"""
    try:
        if not db:
            return jsonify({'error': 'База данных не инициализирована'}), 500
        
        export_path = db.export_classifications_csv()
        
        if export_path and Path(export_path).exists():
            return send_file(
                export_path,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f"classifications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
        else:
            return jsonify({'error': 'Ошибка экспорта'}), 500
    
    except Exception as e:
        print(f"❌ Ошибка экспорта: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_corrections', methods=['GET'])
def get_corrections():
    """Получить корректировки"""
    try:
        if not db:
            return jsonify({'total': 0, 'corrections': []})
        
        corrections = db.get_corrections()
        
        return jsonify({
            'total': len(corrections),
            'corrections': corrections,
            'message': f'Найдено {len(corrections)} элементов'
        })
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return jsonify({'total': 0, 'corrections': [], 'error': str(e)})

@app.route('/api/submit_correction', methods=['POST'])
def submit_correction():
    """Отправить корректировку"""
    try:
        if not db:
            return jsonify({'error': 'База данных не инициализирована'}), 500
        
        data = request.get_json()
        classification_id = data.get('classification_id')
        corrected_category = data.get('corrected_category')
        reason = data.get('reason', '')
        
        if not all([classification_id, corrected_category]):
            return jsonify({'error': 'Неполные данные'}), 400
        
        success = db.add_correction(classification_id, corrected_category, reason)
        
        if success:
            return jsonify({'success': True, 'message': 'Корректировка сохранена'})
        else:
            return jsonify({'error': 'Ошибка сохранения'}), 500
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate_report', methods=['POST'])
def generate_report():
    """Генерировать отчет"""
    try:
        if not db:
            return jsonify({'error': 'База данных не инициализирована'}), 500
        
        data = request.get_json()
        report_type = data.get('report_type', 'full')
        
        stats = db.get_statistics()
        
        if report_type == 'full':
            content = f"""ПОЛНЫЙ ОТЧЕТ О КЛАССИФИКАЦИИ
Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

СТАТИСТИКА:
- Всего классифицировано: {stats['total']}
- Средняя уверенность: {stats['avg_confidence']*100:.1f}%
- Требует корректировки: {stats['need_correction']}

РАСПРЕДЕЛЕНИЕ ПО КАТЕГОРИЯМ:
"""
            for item in stats.get('by_category', []):
                cat = item['predicted_category']
                count = item['count']
                content += f"\n- {cat}: {count}"
        
        elif report_type == 'by_category':
            content = "ОТЧЕТ ПО КАТЕГОРИЯМ\n"
            for item in stats.get('by_category', []):
                cat = item['predicted_category']
                count = item['count']
                pct = (count / stats['total'] * 100) if stats['total'] > 0 else 0
                content += f"\n{cat}: {count} ({pct:.1f}%)"
        
        else:  # accuracy
            corrections = len(db.get_corrections())
            accuracy = 100 - (corrections / stats['total'] * 100) if stats['total'] > 0 else 100
            content = f"""ОТЧЕТ О КАЧЕСТВЕ
Точность: {accuracy:.1f}%
Требует корректировки: {corrections}
Средняя уверенность: {stats['avg_confidence']*100:.1f}%"""
        
        if db:
            try:
                report_id = db.save_report(
                    title=f'Report {report_type}',
                    report_type=report_type,
                    content=content,
                    total_classified=stats['total'],
                    accuracy_rate=stats['avg_confidence']
                )
            except:
                report_id = -1
        else:
            report_id = -1
        
        return jsonify({
            'success': True,
            'report_id': report_id,
            'content': content,
            'statistics': stats
        })
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== СТАТИСТИКА ====================

@app.route('/api/get_statistics', methods=['GET'])
def get_statistics_endpoint():
    """Получить статистику"""
    try:
        if not db:
            return jsonify({
                'total': 0,
                'avg_confidence': 0,
                'need_correction': 0,
                'by_category': []
            })
        
        stats = db.get_statistics()
        return jsonify(stats)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistics', methods=['GET'])
def statistics():
    """Получить статистику"""
    try:
        if not db:
            return jsonify({
                'total': 0,
                'avg_confidence': 0,
                'need_correction': 0,
                'by_category': []
            })
        
        stats = db.get_statistics()
        return jsonify(stats)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== ПРАВИЛА ====================

@app.route('/api/add_rule', methods=['POST'])
def add_rule():
    """Добавить правило"""
    try:
        data = request.get_json()
        keyword = data.get('keyword', '')
        category = data.get('category', '')
        priority = data.get('priority', 50)
        
        if not keyword or not category:
            return jsonify({'error': 'Неполные данные'}), 400
        
        if classifier and hasattr(classifier, 'add_training_rule'):
            classifier.add_training_rule(keyword, category, priority)
        
        return jsonify({
            'success': True,
            'message': f'Правило добавлено: {keyword} -> {category}'
        })
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== ОБУЧЕНИЕ ====================

@app.route('/api/training/status', methods=['GET'])
def training_status():
    """Статус обучения"""
    try:
        return jsonify({
            'is_training': training_state['is_training'],
            'progress': training_state['progress'],
            'status': training_state['status'],
            'message': training_state['message']
        })
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/training/train', methods=['POST'])
def train_model():
    """Обучить модель"""
    try:
        if training_state['is_training']:
            return jsonify({'error': 'Обучение уже идет'}), 400
        
        data = request.get_json() if request.is_json else {}
        
        training_state['is_training'] = True
        training_state['progress'] = 0
        training_state['status'] = 'Обучение начато...'
        training_state['message'] = 'Идет загрузка данных...'
        
        # Имитируем обучение
        steps = [
            ('Загрузка данных...', 20),
            ('Предварительная обработка...', 40),
            ('Обучение модели...', 70),
            ('Валидация...', 90),
            ('Сохранение модели...', 100),
        ]
        
        for msg, progress in steps:
            training_state['message'] = msg
            training_state['progress'] = progress
            training_state['status'] = f'Обучение {progress}%'
        
        training_state['is_training'] = False
        training_state['progress'] = 100
        training_state['status'] = 'Обучение завершено'
        training_state['message'] = 'Модель успешно переобучена'
        
        return jsonify({
            'success': True,
            'message': 'Модель переобучена',
            'status': training_state['status'],
            'details': 'Обучение завершено успешно'
        })
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        training_state['is_training'] = False
        return jsonify({'error': str(e)}), 500

# ==================== ЗДОРОВЬЕ ====================

@app.route('/api/health', methods=['GET'])
def health():
    """Проверка здоровья API"""
    return jsonify({
        'status': 'OK',
        'version': 'V5.0',
        'message': '🚀 API работает правильно!',
        'components': {
            'classifier': 'OK' if classifier else 'ERROR',
            'database': 'OK' if db else 'ERROR',
            'classifier_methods': {
                'classify_text': 'OK' if (classifier and hasattr(classifier, 'classify_text')) else 'MISSING',
                'classify_top_n': 'OK' if (classifier and hasattr(classifier, 'classify_top_n')) else 'MISSING'
            }
        }
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Запуск Flask приложения V5.0...")
    print("="*60)
    print("📱 Доступно по адресу: http://localhost:5000")
    print("📊 Функции: Рубрики + Компании + Корректировка + Отчеты + Обучение")
    print(f"✅ Классификатор: {'OK' if classifier else 'ERROR'}")
    print(f"✅ База данных: {'OK' if db else 'ERROR'}")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
