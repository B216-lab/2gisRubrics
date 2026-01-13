# database_ИСПРАВЛЕННЫЙ_V2.py
"""
Исправленная БД с правильной схемой и миграцией
- ✅ Добавлен predicted_category
- ✅ Добавлена миграция таблиц
- ✅ Исправлена схема классификаций
"""

import sqlite3
from pathlib import Path
from datetime import datetime
import json

DATABASE_DIR = Path("data")
DATABASE_FILE = DATABASE_DIR / "classifier.db"

class Database:
    """Управление БД классификаций"""
    
    def __init__(self):
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        self.db_path = DATABASE_FILE
        self.init_db()
    
    def get_connection(self):
        """Получить подключение к БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Инициализировать БД с правильной схемой"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # ✅ ТАБЛИЦА: companies
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    rubrics TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ✅ ТАБЛИЦА: classifications (ПРАВИЛЬНАЯ СХЕМА!)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS classifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER,
                    company_name TEXT NOT NULL,
                    text TEXT NOT NULL,
                    predicted_category TEXT,
                    confidence REAL DEFAULT 0.0,
                    top_3 TEXT,
                    rules_applied BOOLEAN DEFAULT 0,
                    correction_needed BOOLEAN DEFAULT 0,
                    corrected_category TEXT,
                    correction_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(company_id) REFERENCES companies(id)
                )
            ''')
            
            # ✅ ТАБЛИЦА: training_data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS training_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    category TEXT NOT NULL,
                    source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ✅ ТАБЛИЦА: corrections (для корректировки)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS corrections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    classification_id INTEGER NOT NULL,
                    original_category TEXT,
                    corrected_category TEXT,
                    reason TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(classification_id) REFERENCES classifications(id)
                )
            ''')
            
            # ✅ ТАБЛИЦА: reports
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    report_type TEXT,
                    content TEXT,
                    total_classified INTEGER DEFAULT 0,
                    accuracy_rate REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            print("✅ БД инициализирована с правильной схемой")
            
        except Exception as e:
            print(f"❌ Ошибка инициализации БД: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def migrate_tables(self):
        """Миграция таблиц - добавить недостающие колонки"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Проверяем наличие колонок в classifications
            cursor.execute("PRAGMA table_info(classifications)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Добавляем missing колонки
            migrations = [
                ('predicted_category', "ALTER TABLE classifications ADD COLUMN predicted_category TEXT"),
                ('confidence', "ALTER TABLE classifications ADD COLUMN confidence REAL DEFAULT 0.0"),
                ('top_3', "ALTER TABLE classifications ADD COLUMN top_3 TEXT"),
                ('rules_applied', "ALTER TABLE classifications ADD COLUMN rules_applied BOOLEAN DEFAULT 0"),
                ('correction_needed', "ALTER TABLE classifications ADD COLUMN correction_needed BOOLEAN DEFAULT 0"),
                ('corrected_category', "ALTER TABLE classifications ADD COLUMN corrected_category TEXT"),
                ('correction_reason', "ALTER TABLE classifications ADD COLUMN correction_reason TEXT"),
            ]
            
            for col_name, sql in migrations:
                if col_name not in columns:
                    try:
                        cursor.execute(sql)
                        print(f"✅ Добавлена колонка: {col_name}")
                    except sqlite3.OperationalError as e:
                        if 'already exists' not in str(e):
                            print(f"⚠️ {col_name}: {e}")
            
            conn.commit()
            print("✅ Миграция завершена")
            
        except Exception as e:
            print(f"❌ Ошибка миграции: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def save_classification(self, company_id: int = None, company_name: str = "", 
                           text: str = "", predicted_category: str = "", 
                           confidence: float = 0.0, top_3: list = None, 
                           rules_applied: bool = False):
        """Сохранить результат классификации"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            top_3_json = json.dumps(top_3) if top_3 else "[]"
            
            cursor.execute('''
                INSERT INTO classifications 
                (company_id, company_name, text, predicted_category, confidence, top_3, rules_applied, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                company_id,
                company_name,
                text,
                predicted_category,
                confidence,
                top_3_json,
                1 if rules_applied else 0,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"❌ Ошибка сохранения классификации: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def save_company(self, name: str, description: str = "", rubrics: str = ""):
        """Сохранить компанию"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO companies (name, description, rubrics, created_at)
                VALUES (?, ?, ?, ?)
            ''', (name, description, rubrics, datetime.now().isoformat()))
            
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"❌ Ошибка сохранения компании: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def get_classifications(self, limit: int = 100, offset: int = 0):
        """Получить классификации"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT * FROM classifications 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"❌ Ошибка получения классификаций: {e}")
            return []
        finally:
            conn.close()
    
    def get_corrections(self, status: str = 'pending'):
        """Получить классификации на корректировку"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT c.*, co.original_category, co.corrected_category 
                FROM classifications c
                LEFT JOIN corrections co ON c.id = co.classification_id
                WHERE c.correction_needed = 1 OR c.corrected_category IS NOT NULL
                ORDER BY c.created_at DESC
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"❌ Ошибка получения корректировок: {e}")
            return []
        finally:
            conn.close()
    
    def add_correction(self, classification_id: int, corrected_category: str, reason: str = ""):
        """Добавить корректировку"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Получить оригинальную категорию
            cursor.execute('SELECT predicted_category FROM classifications WHERE id = ?', (classification_id,))
            row = cursor.fetchone()
            original_category = row['predicted_category'] if row else ""
            
            # Сохранить корректировку
            cursor.execute('''
                INSERT INTO corrections 
                (classification_id, original_category, corrected_category, reason, status)
                VALUES (?, ?, ?, ?, 'completed')
            ''', (classification_id, original_category, corrected_category, reason))
            
            # Обновить классификацию
            cursor.execute('''
                UPDATE classifications 
                SET corrected_category = ?, correction_reason = ?, correction_needed = 0
                WHERE id = ?
            ''', (corrected_category, reason, classification_id))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Ошибка добавления корректировки: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def save_report(self, title: str, report_type: str, content: str, 
                   total_classified: int = 0, accuracy_rate: float = 0.0):
        """Сохранить отчет"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO reports 
                (title, report_type, content, total_classified, accuracy_rate, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (title, report_type, content, total_classified, accuracy_rate, datetime.now().isoformat()))
            
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"❌ Ошибка сохранения отчета: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def get_statistics(self):
        """Получить статистику"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Всего классификаций
            cursor.execute('SELECT COUNT(*) as count FROM classifications')
            total = cursor.fetchone()['count']
            
            # Средняя уверенность
            cursor.execute('SELECT AVG(confidence) as avg_conf FROM classifications')
            avg_confidence = cursor.fetchone()['avg_conf'] or 0.0
            
            # Требующие корректировки
            cursor.execute('SELECT COUNT(*) as count FROM classifications WHERE correction_needed = 1')
            need_correction = cursor.fetchone()['count']
            
            # По категориям
            cursor.execute('''
                SELECT predicted_category, COUNT(*) as count 
                FROM classifications 
                GROUP BY predicted_category 
                ORDER BY count DESC
            ''')
            by_category = [dict(row) for row in cursor.fetchall()]
            
            return {
                'total': total,
                'avg_confidence': round(avg_confidence, 2),
                'need_correction': need_correction,
                'by_category': by_category
            }
        except Exception as e:
            print(f"❌ Ошибка получения статистики: {e}")
            return {}
        finally:
            conn.close()
    
    def export_classifications_csv(self, filepath: str = None):
        """Экспортировать классификации в CSV"""
        try:
            import pandas as pd
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, company_name, text, predicted_category, confidence, 
                       rules_applied, correction_needed, corrected_category, created_at
                FROM classifications 
                ORDER BY created_at DESC
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            # Преобразуем в DataFrame
            data = []
            for row in rows:
                data.append({
                    'ID': row['id'],
                    'Компания': row['company_name'],
                    'Текст': row['text'],
                    'Предсказанная категория': row['predicted_category'],
                    'Уверенность': f"{row['confidence']*100:.1f}%",
                    'Использованы правила': 'Да' if row['rules_applied'] else 'Нет',
                    'Требует корректировки': 'Да' if row['correction_needed'] else 'Нет',
                    'Скорректированная категория': row['corrected_category'] or '',
                    'Дата': row['created_at']
                })
            
            df = pd.DataFrame(data)
            
            if filepath is None:
                filepath = DATABASE_DIR / f"classifications_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            print(f"✅ Экспорт завершен: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Ошибка экспорта: {e}")
            return None
