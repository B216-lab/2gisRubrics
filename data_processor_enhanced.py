# data_processor_enhanced.py
"""
Расширенный обработчик данных с поддержкой TXT, Excel и экспорта в исходный файл
"""

import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Tuple
import openpyxl

class DataProcessorEnhanced:
    """Расширенный обработчик данных"""
    
    SUPPORTED_FORMATS = ['.csv', '.txt', '.xlsx', '.xls']
    
    @staticmethod
    def load_file(filepath: str) -> Tuple[List[str], str]:
        """
        Загрузить данные из файла
        Возвращает: (список элементов, формат файла)
        """
        path = Path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"Файл не найден: {filepath}")
        
        suffix = path.suffix.lower()
        
        if suffix == '.csv':
            return DataProcessorEnhanced._load_csv(filepath), 'csv'
        elif suffix == '.txt':
            return DataProcessorEnhanced._load_txt(filepath), 'txt'
        elif suffix in ['.xlsx', '.xls']:
            return DataProcessorEnhanced._load_excel(filepath), 'excel'
        else:
            raise ValueError(f"Неподдерживаемый формат: {suffix}")
    
    @staticmethod
    def _load_csv(filepath: str) -> List[str]:
        """Загрузить CSV файл"""
        df = pd.read_csv(filepath, encoding='utf-8')
        # Берем первый столбец
        return df.iloc[:, 0].astype(str).tolist()
    
    @staticmethod
    def _load_txt(filepath: str) -> List[str]:
        """Загрузить TXT файл"""
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        return lines
    
    @staticmethod
    def _load_excel(filepath: str) -> List[str]:
        """Загрузить Excel файл"""
        df = pd.read_excel(filepath)
        # Берем первый столбец
        return df.iloc[:, 0].astype(str).tolist()
    
    @staticmethod
    def export_with_results(original_file: str, results: List[Dict], 
                           output_file: str = None) -> str:
        """
        Экспортировать результаты добавив категорию в исходный файл
        
        Args:
            original_file: путь к исходному файлу
            results: список результатов с ключами: input_text, category, confidence
            output_file: путь к выходному файлу (опционально)
        
        Returns:
            путь к созданному файлу
        """
        path = Path(original_file)
        
        if output_file is None:
            # Создаем имя выходного файла
            output_file = str(path.parent / f"{path.stem}_classified{path.suffix}")
        
        suffix = path.suffix.lower()
        
        if suffix == '.csv':
            return DataProcessorEnhanced._export_csv(original_file, results, output_file)
        elif suffix == '.txt':
            return DataProcessorEnhanced._export_txt(original_file, results, output_file)
        elif suffix in ['.xlsx', '.xls']:
            return DataProcessorEnhanced._export_excel(original_file, results, output_file)
        else:
            raise ValueError(f"Неподдерживаемый формат: {suffix}")
    
    @staticmethod
    def _export_csv(original_file: str, results: List[Dict], output_file: str) -> str:
        """Экспортировать в CSV"""
        # Читаем исходный файл
        df = pd.read_csv(original_file, encoding='utf-8')
        
        # Добавляем новые столбцы
        categories = [r['category'] for r in results]
        confidences = [r['confidence'] for r in results]
        
        df['predicted_category'] = categories
        df['confidence'] = confidences
        
        # Если есть top_3, добавляем еще один столбец
        if 'top_3' in results[0]:
            top_3_str = []
            for r in results:
                top_3 = '; '.join([f"{cat} ({conf:.1%})" for cat, conf in r['top_3']])
                top_3_str.append(top_3)
            df['top_3_variants'] = top_3_str
        
        # Сохраняем
        df.to_csv(output_file, index=False, encoding='utf-8')
        return output_file
    
    @staticmethod
    def _export_txt(original_file: str, results: List[Dict], output_file: str) -> str:
        """Экспортировать в TXT"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("Текст | Категория | Уверенность | Топ-3\n")
            f.write("=" * 100 + "\n")
            
            for r in results:
                text = r['input_text'][:50]  # Первые 50 символов
                category = r['category']
                confidence = f"{r['confidence']:.1%}"
                
                top_3 = ""
                if 'top_3' in r:
                    top_3 = "; ".join([f"{cat} ({conf:.1%})" for cat, conf in r['top_3']])
                
                f.write(f"{text:50} | {category:30} | {confidence:10} | {top_3}\n")
        
        return output_file
    
    @staticmethod
    def _export_excel(original_file: str, results: List[Dict], output_file: str) -> str:
        """Экспортировать в Excel"""
        # Читаем исходный файл
        df = pd.read_excel(original_file)
        
        # Добавляем новые столбцы
        categories = [r['category'] for r in results]
        confidences = [r['confidence'] for r in results]
        
        df['predicted_category'] = categories
        df['confidence'] = confidences
        
        # Если есть top_3, добавляем еще один столбец
        if 'top_3' in results[0]:
            top_3_str = []
            for r in results:
                top_3 = '; '.join([f"{cat} ({conf:.1%})" for cat, conf in r['top_3']])
                top_3_str.append(top_3)
            df['top_3_variants'] = top_3_str
        
        # Сохраняем с форматированием
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
            
            # Форматирование (опционально)
            workbook = writer.book
            worksheet = writer.sheets['Sheet1']
            
            # Автоширина столбцов
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        return output_file
    
    @staticmethod
    def get_file_type(filepath: str) -> str:
        """Определить тип файла"""
        path = Path(filepath)
        suffix = path.suffix.lower()
        
        if suffix == '.csv':
            return 'CSV'
        elif suffix == '.txt':
            return 'TXT'
        elif suffix in ['.xlsx', '.xls']:
            return 'Excel'
        else:
            return 'Unknown'

# Функция для быстрого экспорта
def quick_export(original_file: str, results: List[Dict], 
                output_dir: str = 'output') -> str:
    """
    Быстрый экспорт результатов
    
    Args:
        original_file: исходный файл
        results: список результатов классификации
        output_dir: папка для результатов
    
    Returns:
        путь к файлу результатов
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    original_path = Path(original_file)
    output_file = str(Path(output_dir) / f"{original_path.stem}_classified{original_path.suffix}")
    
    return DataProcessorEnhanced.export_with_results(original_file, results, output_file)
