# ui.py
"""CLI интерфейс - ИСПРАВЛЕННАЯ ВЕРСИЯ с меню 0 и 2"""

import os
from colorama import Fore, Back, Style, init
from pathlib import Path
import pandas as pd
from data_processor import DataProcessor
from classifier import CompanyClassifier
from training_manager import TrainingManager, RubricClassifier

init(autoreset=True)

class CLI:
    def __init__(self):
        self.processor = DataProcessor()
        self.classifier = CompanyClassifier()
        self.trainer = TrainingManager()
        self.rubric_classifier = RubricClassifier()
    
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_banner(self):
        print(f"""{Fore.CYAN}{Back.BLACK}
╔══════════════════════════════════════════════════════════════╗
║         🎯 Classification System Pro v2.0 FIXED             ║
║    Система классификации рубрик с ручным обучением          ║
║              Для данных из 2GIS (parser-2gis)               ║
╚══════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}
        """)
    
    def print_menu(self):
        print(f"""{Fore.YELLOW}
╔═══════════════════ ГЛАВНОЕ МЕНЮ ═══════════════════╗
║                                                    ║
║  0. 📊 Обучить модель (ПЕРВЫЙ РАЗ!)               ║
║  1. 📂 Загрузить компании из CSV                   ║
║  2. 🔍 Классифицировать РУБРИКИ (НОВОЕ!)          ║
║  3. 🔄 Классифицировать КОМПАНИИ                  ║
║  4. 📊 Генерировать отчет                          ║
║  5. 📚 Управление правилами обучения               ║
║  6. ✓  Проверка и корректировка                    ║
║  7. 📥 Экспортировать результаты                   ║
║  8. 📋 Справочник категорий                        ║
║  9. ❌ Выход                                       ║
║                                                    ║
╚════════════════════════════════════════════════════╝
{Style.RESET_ALL}
        """)
    
    def menu_train_model(self):
        print(f"{Fore.CYAN}📊 Обучение модели{Style.RESET_ALL}")
        filepath = input("Путь к файлу компаний (data/companies.csv): ").strip() or "data/companies.csv"
        
        if not Path(filepath).exists():
            print(f"{Fore.RED}✗ Файл не найден: {filepath}{Style.RESET_ALL}")
            return
        
        try:
            self.trainer.train_model(filepath)
            print(f"{Fore.GREEN}✓ Модель успешно обучена!{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}✗ Ошибка при обучении: {e}{Style.RESET_ALL}")
    
    def menu_load_companies(self):
        print(f"{Fore.CYAN}📂 Загрузка компаний{Style.RESET_ALL}")
        filepath = input("Путь к файлу (data/companies.csv): ").strip() or "data/companies.csv"
        
        if not Path(filepath).exists():
            print(f"{Fore.RED}✗ Файл не найден: {filepath}{Style.RESET_ALL}")
            return
        
        try:
            self.processor.load_companies(filepath)
            print(f"{Fore.GREEN}✓ Компании успешно загружены{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}✗ Ошибка при загрузке: {e}{Style.RESET_ALL}")
    
    def menu_classify_rubrics(self):
        print(f"{Fore.CYAN}🔍 Классификация рубрик{Style.RESET_ALL}")
        
        print("""
Способы классификации рубрик:
1. ⌨  Ввести одну рубрику вручную
2. 📁 Загрузить рубрики из файла CSV
3. ↩  Назад
        """)
        
        choice = input("Выберите способ (1-3): ").strip()
        
        if choice == '1':
            self._classify_single_rubric()
        elif choice == '2':
            self._classify_rubrics_from_file()
        elif choice == '3':
            return
        else:
            print(f"{Fore.RED}✗ Неверный выбор{Style.RESET_ALL}")
    
    def _classify_single_rubric(self):
        print(f"\n{Fore.CYAN}Введите рубрику{Style.RESET_ALL}")
        rubric = input("Рубрика: ").strip()
        
        if not rubric:
            print(f"{Fore.RED}✗ Рубрика не указана{Style.RESET_ALL}")
            return
        
        if self.classifier.classifier.vectorizer is None:
            print(f"{Fore.YELLOW}⏳ Загрузка модели...{Style.RESET_ALL}")
            if not self.classifier.classifier.load_model():
                print(f"{Fore.RED}✗ Модель не найдена. Обучите модель сначала (меню 0){Style.RESET_ALL}")
                return
        
        try:
            category, confidence = self.classifier.classifier.classify_text(rubric)
            top_3 = self.classifier.classifier.classify_top_n(rubric, n=3)
            
            print(f"\n{Fore.GREEN}📊 Результаты классификации:{Style.RESET_ALL}")
            print(f"  Рубрика: {Fore.CYAN}{rubric}{Style.RESET_ALL}")
            print(f"  Финальная категория: {Fore.GREEN}{category}{Style.RESET_ALL}")
            print(f"  Уверенность: {Fore.YELLOW}{confidence:.1%}{Style.RESET_ALL}")
            print(f"\n  Топ-3 варианта:")
            for i, (cat, conf) in enumerate(top_3, 1):
                print(f"    {i}. {cat}: {Fore.YELLOW}{conf:.1%}{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}✗ Ошибка: {e}{Style.RESET_ALL}")
    
    def _classify_rubrics_from_file(self):
        print(f"\n{Fore.CYAN}Формат файла: CSV с рубриками{Style.RESET_ALL}")
        filepath = input("Путь к файлу: ").strip()
        
        if not Path(filepath).exists():
            print(f"{Fore.RED}✗ Файл не найден{Style.RESET_ALL}")
            return
        
        try:
            df = pd.read_csv(filepath, encoding='utf-8')
            rubrics = df.iloc[:, 0].tolist()
            
            print(f"\n{Fore.CYAN}Классификация {len(rubrics)} рубрик...{Style.RESET_ALL}")
            
            if self.classifier.classifier.vectorizer is None:
                if not self.classifier.classifier.load_model():
                    print(f"{Fore.RED}✗ Модель не найдена{Style.RESET_ALL}")
                    return
            
            results = []
            for rubric in rubrics:
                category, confidence = self.classifier.classifier.classify_text(str(rubric))
                results.append({
                    'rubric': rubric,
                    'category': category,
                    'confidence': confidence
                })
            
            output_file = 'output/rubrics_classified.csv'
            Path('output').mkdir(exist_ok=True)
            pd.DataFrame(results).to_csv(output_file, index=False, encoding='utf-8')
            
            print(f"{Fore.GREEN}✓ Результаты сохранены в {output_file}{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}✗ Ошибка: {e}{Style.RESET_ALL}")
    
    def menu_classify_companies(self):
        print(f"{Fore.CYAN}🔄 Классификация компаний{Style.RESET_ALL}")
        
        if self.processor.companies_df is None:
            print(f"{Fore.RED}✗ Сначала загрузите компании (меню 1){Style.RESET_ALL}")
            return
        
        use_cache = input("Использовать кэшированную модель? (y/n, default: y): ").lower() != 'n'
        
        try:
            self.processor.classify_companies(load_cached_model=use_cache)
            print(f"{Fore.GREEN}✓ Классификация завершена{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}✗ Ошибка при классификации: {e}{Style.RESET_ALL}")
    
    def menu_report(self):
        print(f"{Fore.CYAN}📊 Генерирование отчета{Style.RESET_ALL}")
        
        if self.processor.classified_df is None:
            print(f"{Fore.RED}✗ Сначала классифицируйте компании{Style.RESET_ALL}")
            return
        
        try:
            self.processor.generate_report()
            print(f"{Fore.GREEN}✓ Отчет сгенерирован{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}✗ Ошибка при генерировании отчета: {e}{Style.RESET_ALL}")
    
    def menu_training_rules(self):
        print(f"""{Fore.YELLOW}
╔════════════ ПРАВИЛА ОБУЧЕНИЯ ════════════╗
║  1. ➕ Добавить новое правило            ║
║  2. 📋 Просмотреть все правила           ║
║  3. 🗑  Удалить правило                  ║
║  4. ↩  Назад                             ║
╚══════════════════════════════════════════╝
{Style.RESET_ALL}
        """)
        
        choice = input("Выберите действие (1-4): ").strip()
        
        if choice == '1':
            keyword = input("Ключевое слово: ").strip()
            category = input("Категория: ").strip()
            try:
                priority = int(input("Приоритет (1-100, default: 50): ") or "50")
            except:
                priority = 50
            
            self.classifier.classifier.add_training_rule(keyword, category, priority)
            print(f"{Fore.GREEN}✓ Правило добавлено{Style.RESET_ALL}")
        
        elif choice == '2':
            rules = self.classifier.classifier.training_rules.get('rules', [])
            if not rules:
                print(f"{Fore.YELLOW}Нет правил обучения{Style.RESET_ALL}")
            else:
                print(f"\n{Fore.CYAN}📋 Активные правила:{Style.RESET_ALL}")
                for i, rule in enumerate(rules, 1):
                    print(f"{i}. '{rule['keyword']}' → {Fore.GREEN}{rule['category']}{Style.RESET_ALL} "
                          f"(приоритет: {rule['priority']})")
    
    def menu_verification(self):
        print(f"{Fore.CYAN}✓ Проверка и корректировка{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Функция в разработке{Style.RESET_ALL}")
    
    def menu_export(self):
        print(f"{Fore.CYAN}📥 Экспортировать результаты{Style.RESET_ALL}")
        
        if self.processor.classified_df is None:
            print(f"{Fore.RED}✗ Нет данных для экспорта{Style.RESET_ALL}")
            return
        
        print("""
1. 📊 CSV (классифицированные данные)
2. 📋 JSON (отчет)
3. ↩  Назад
        """)
        
        choice = input("Выберите формат (1-3): ").strip()
        
        if choice == '1':
            filepath = input("Путь к файлу (output/classified.csv): ").strip() or "output/classified.csv"
            self.processor.save_classified(filepath)
        elif choice == '2':
            filepath = input("Путь к файлу (output/report.json): ").strip() or "output/report.json"
            self.processor.generate_report(filepath)
    
    def menu_categories(self):
        print(f"{Fore.CYAN}📋 СПРАВОЧНИК КАТЕГОРИЙ{Style.RESET_ALL}")
        try:
            df = pd.read_csv('data/categories.csv', sep=';', encoding='utf-8')
            print(f"\nВсего категорий: {len(df)}\n")
            for idx, row in df.head(10).iterrows():
                print(f"{row['№']}. {Fore.GREEN}{row['Тип']}{Style.RESET_ALL}")
                if pd.notna(row['Общее описание']):
                    print(f"   {row['Общее описание']}\n")
        except Exception as e:
            print(f"{Fore.RED}✗ Ошибка: {e}{Style.RESET_ALL}")
    
    def run(self):
        while True:
            self.clear_screen()
            self.print_banner()
            self.print_menu()
            
            choice = input(f"{Fore.YELLOW}Выберите действие (0-9): {Style.RESET_ALL}").strip()
            
            if choice == '0':
                self.menu_train_model()
            elif choice == '1':
                self.menu_load_companies()
            elif choice == '2':
                self.menu_classify_rubrics()
            elif choice == '3':
                self.menu_classify_companies()
            elif choice == '4':
                self.menu_report()
            elif choice == '5':
                self.menu_training_rules()
            elif choice == '6':
                self.menu_verification()
            elif choice == '7':
                self.menu_export()
            elif choice == '8':
                self.menu_categories()
            elif choice == '9':
                print(f"{Fore.CYAN}До свидания!{Style.RESET_ALL}")
                break
            else:
                print(f"{Fore.RED}✗ Неверный выбор{Style.RESET_ALL}")
            
            input(f"\n{Fore.YELLOW}Нажмите Enter для продолжения...{Style.RESET_ALL}")

if __name__ == '__main__':
    cli = CLI()
    cli.run()
