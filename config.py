# config_FIXED.py
"""
Исправленная конфигурация - добавлена MIN_CONFIDENCE_THRESHOLD
"""

from pathlib import Path

# Базовые пути
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = 'data'
MODELS_DIR = 'models'
OUTPUT_DIR = 'output'

# Убедиться что папки существуют
Path(DATA_DIR).mkdir(exist_ok=True)
Path(MODELS_DIR).mkdir(exist_ok=True)
Path(OUTPUT_DIR).mkdir(exist_ok=True)

# Файлы данных
CATEGORIES_FILE = 'data/categories.csv'
COMPANIES_FILE = 'data/companies.csv'
TRAINING_RULES_FILE = 'models/training_rules.json'

# Выходные файлы
CLASSIFIED_OUTPUT = 'output/classified_companies.csv'
RUBRICS_OUTPUT = 'output/rubrics_classified.csv'
REPORT_OUTPUT = 'output/report.json'
REPORT_FILE = 'output/reportt.json'
UPLOAD_FOLDER = "upload"

# ML параметры
MIN_CONFIDENCE_THRESHOLD = 0.5  # ✅ ИСПРАВЛЕНО: добавлена недостающая переменная
MAX_FEATURES = 5000
N_ESTIMATORS = 200
MAX_DEPTH = 15
RANDOM_STATE = 42

# Логирование
LOG_LEVEL = 'INFO'
LOG_FILE = 'output/classification.log'

print(f"✓ Конфигурация загружена")
print(f"  Data dir: {Path(DATA_DIR).absolute()}")
print(f"  Models dir: {Path(MODELS_DIR).absolute()}")
print(f"  Output dir: {Path(OUTPUT_DIR).absolute()}")
