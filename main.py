import os
import re
import pandas as pd
import gzip
from datetime import datetime
import time

# --- КОНФИГУРАЦИЯ ---

# 1. Путь к папке с логами (Замените на свой!)
ROOT_LOG_DIR = r'C:\logs\SA004444' 

# 2. Дата начала (файлы старше этой даты игнорируются)
START_DATE_STR = '2025-01-01'
START_DATE = datetime.strptime(START_DATE_STR, '%Y-%m-%d').timestamp()

# 3. Полный список метрик
METRICS_LIST = [
    # --- SEARCH BY ID (Стандартный поиск по номеру теста) ---
    ('49.2.2', 'VDD_ASIC1_VOUT_Voltage'), 
    ('49.2.3', 'VDD_ASIC1_VOUT_Current'),
    ('49.2.12', 'VDD_ASIC2_VOUT_Voltage'), 
    ('49.2.13', 'VDD_ASIC2_VOUT_Current'),

    # --- SEARCH BY NAME (Поиск по имени, когда ID = N/A) ---
    ('asic1_asic_total_power', 'ASIC1_Total_Power'),
    ('asic2_asic_total_power', 'ASIC2_Total_Power'),
]

# --- ЛОГИКА ---

def get_regex_pattern(search_key):
    """
    Автоматически выбирает Regex:
    - Если ключ это ID (цифры.точки) -> ищем во 2-й колонке.
    - Если ключ это Текст -> ищем в 1-й колонке (прыгаем через N/A).
    """
    escaped_key = re.escape(search_key)
    
    # Проверка: состоит ли ключ только из цифр и точек? (например 49.2.12)
    if re.match(r'^\d+(\.\d+)*$', search_key):
        # Логика для ID: Значение через 2 разделителя (| Desc | Val)
        pattern = rf"{escaped_key}\s*[│|].*?[│|]\s*([-+]?\d*\.?\d+)"
    else:
        # Логика для Имени: Значение через 3 разделителя (| N/A | Desc | Val)
        pattern = rf"{escaped_key}\s*[│|].*?[│|].*?[│|]\s*([-+]?\d*\.?\d+)"
        
    return pattern

def parse_log_file(filepath):
    data = {
        'Filename': os.path.basename(filepath),
        'Date': time.ctime(os.path.getmtime(filepath))
    }
    
    # Инициализация колонок (None по умолчанию)
    for _, name in METRICS_LIST:
        data[name] = None

    try:
        # Открываем как .gz или как обычный текст
        if filepath.endswith('.gz'):
            opener = gzip.open
            mode = 'rt' # rt = read text
        else:
            opener = open
            mode = 'r'

        with opener(filepath, mode, encoding='utf-8', errors='ignore') as f:
            content = f.read()

            # Группируем метрики (на случай дубликатов ключей)
            metrics_map = {}
            for search_key, col_name in METRICS_LIST:
                if search_key not in metrics_map:
                    metrics_map[search_key] = []
                metrics_map[search_key].append(col_name)

            # Проходим по каждому ключу поиска
            for search_key, col_names in metrics_map.items():
                pattern = get_regex_pattern(search_key)
                
                # Ищем ВСЕ вхождения в файле
                matches = re.findall(pattern, content)
                
                # Записываем данные в колонки по очереди
                for i, val in enumerate(matches):
                    if i < len(col_names):
                        col_name = col_names[i]
                        try:
                            data[col_name] = float(val)
                        except ValueError:
                            data[col_name] = val # Если не число, пишем как текст
                            
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None

    # Проверка на полноту данных: если хоть одна метрика None -> игнорируем файл
    for _, name in METRICS_LIST:
        if data[name] is None:
            # Опционально: можно раскомментировать для отладки
            # print(f"Skipping {data['Filename']}: missing {name}")
            return None

    return data

def main():
    results = []
    print(f"--- ЗАПУСК ПАРСЕРА ---")
    print(f"Папка: {ROOT_LOG_DIR}")
    print(f"Фильтр даты: {START_DATE_STR}")
    print("Фильтр имен: исключаем 'SUMMARY' и 'led'")
    
    scanned_count = 0
    skipped_count = 0
    
    # Рекурсивный обход папок
    for root, dirs, files in os.walk(ROOT_LOG_DIR):
        for file in files:
            # 1. Фильтр расширения
            if not file.endswith((".log", ".txt", ".gz")):
                continue
            
            # 2. Фильтр по имени (исключаем лишние)
            if "SUMMARY" in file or "led" in file:
                skipped_count += 1
                continue

            # 3. Фильтр по дате модификации
            filepath = os.path.join(root, file)
            if os.path.getmtime(filepath) >= START_DATE:
                scanned_count += 1
                parsed = parse_log_file(filepath)
                if parsed:
                    results.append(parsed)
                    # Вывод прогресса каждые 50 файлов (чтобы не спамить)
                    if scanned_count % 50 == 0:
                        print(f"Обработано {scanned_count} файлов...")

    print(f"\nГотово. Просканировано файлов: {scanned_count}. Пропущено (SUMMARY/led): {skipped_count}")

    if results:
        df = pd.DataFrame(results)
        
        # Сортировка колонок для красоты (Имя -> Дата -> Метрики по порядку)
        metric_cols = [item[1] for item in METRICS_LIST]
        final_cols = ['Filename', 'Date'] + metric_cols
        # Оставляем только те, что реально создались
        final_cols = [c for c in final_cols if c in df.columns]
        df = df[final_cols]

        print("\n" + "="*80)
        print("РЕЗУЛЬТАТ (Первые 5 строк):")
        print("="*80)
        print(df.head(5).to_string())

        # Сохранение
        output_csv = 'ft_metrics_final.csv'
        df.to_csv(output_csv, index=False)
        print(f"\n[OK] Полный отчет сохранен в файл: {os.path.abspath(output_csv)}")
        
        # Опционально: Excel
        # df.to_excel('ft_metrics_final.xlsx', index=False)
    else:
        print("\n[WARN] Результатов нет. Проверьте путь к папке и дату.")

if __name__ == "__main__":
    main()