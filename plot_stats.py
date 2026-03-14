import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import expon, chi2
import matplotlib
import os
import warnings

# Вимикаємо попередження pandas для чистоти консолі
warnings.filterwarnings('ignore')

# --- Налаштування шрифтів (Академічний стиль) ---
matplotlib.rcParams['font.family'] = 'Times New Roman'
matplotlib.rcParams['font.size'] = 12

print("ЗБІР ДАНИХ З УСІХ 25 ПРОГОНІВ...")

# =====================================================================
# ЧАСТИНА 1: ЗБІР УСІЄЇ СТАТИСТИКИ (ДЛЯ ДОДАТКУ А ТА РОЗДІЛУ 4)
# =====================================================================
all_data = []

for set_idx in range(5):
    for run in range(1, 6):
        file_path = f"Set_{set_idx}/Run_{run}/simulation_stats.csv"
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            df_stable = df[df['Time'] > 60000] # Відкидаємо перехідний період динамічно
            
            mean_crush_util = df_stable['Crusher Utilization'].mean()
            std_crush_util = df_stable['Crusher Utilization'].std()
            
            mean_crush_q = df_stable['Average Crusher Queue'].mean()
            std_crush_q = df_stable['Average Crusher Queue'].std()
            
            mean_exc_util = df_stable['Excavator 1 Utilization'].mean()
            std_exc_util = df_stable['Excavator 1 Utilization'].std()
            
            all_data.append({
                'Set': set_idx, 'Run': run,
                'Mean_Crush_Util': mean_crush_util, 'Std_Crush_Util': std_crush_util,
                'Mean_Crush_Q': mean_crush_q, 'Std_Crush_Q': std_crush_q,
                'Mean_Exc_Util': mean_exc_util, 'Std_Exc_Util': std_exc_util
            })

df_results = pd.DataFrame(all_data)
global_means = df_results.groupby('Set')[['Mean_Crush_Util', 'Mean_Crush_Q', 'Mean_Exc_Util']].mean().reset_index() if not df_results.empty else pd.DataFrame()

# =====================================================================
# ЧАСТИНА 2: ВИВІД ДЛЯ РОЗДІЛУ 4 (ЕКСПЕРИМЕНТИ ТА ГРАФІКИ)
# =====================================================================
print("\n" + "="*50)
print("=== РОЗДІЛ 4: ЕКСПЕРИМЕНТАЛЬНЕ ДОСЛІДЖЕННЯ ===")
print("="*50)

if not global_means.empty:
    print("\nТаблиця 4.1 - Середні показники стаціонарного режиму для 5 сценаріїв:")
    print(f"{'Сценарій (Set)':<25} | {'Завант. Дробівки':<20} | {'Черга Дробівки':<15} | {'Завант. Екск. 1':<15}")
    print("-" * 80)
    
    scenario_names = ["Set_0 (Базовий)", "Set_1 (Повільна дробівка)", "Set_2 (Швидкі екскаватори)", "Set_3 (Збільшення парку)", "Set_4 (Без пріоритету)"]
    for idx, row in global_means.iterrows():
        print(f"{scenario_names[int(row['Set'])]:<25} | {row['Mean_Crush_Util']:<20.4f} | {row['Mean_Crush_Q']:<15.4f} | {row['Mean_Exc_Util']:<15.4f}")

base_dir = "Set_0/Run_1"
if os.path.exists(f"{base_dir}/simulation_stats.csv"):
    print(f"\n--- Побудова графіків для базового сценарію ({base_dir}) ---")
    df_stats = pd.read_csv(f"{base_dir}/simulation_stats.csv")
    df_wait = pd.read_csv(f"{base_dir}/wait_times.csv")
    
    # --- Графік 1: Динаміка черг ---
    plt.figure(figsize=(10, 5))
    plt.plot(df_stats['Time'], df_stats['Average Crusher Queue'], color='#d62728', linewidth=2.5, label='Дробівка')
    # Залишаємо тільки Екскаватор 1
    plt.plot(df_stats['Time'], df_stats['Excavator 1 Average Queue'], color='#1f77b4', linewidth=2, label='Екскаватор 1')
    
    plt.title('Залежність середньої довжини черг від часу моделювання', fontweight='bold')
    plt.xlabel('Час моделювання (хв)')
    plt.ylabel('Середня кількість вантажівок')
    plt.legend(title='Ресурс:', loc='upper right')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig('average_queues_run1.svg', format='svg')
    plt.close()

    # --- Графік 2: Динаміка завантаження ---
    plt.figure(figsize=(10, 5))
    plt.plot(df_stats['Time'], df_stats['Crusher Utilization'], color='#d62728', linewidth=2.5, label='Дробівка')
    # Залишаємо тільки Екскаватор 1
    plt.plot(df_stats['Time'], df_stats['Excavator 1 Utilization'], color='#1f77b4', linewidth=2, label='Екскаватор 1')
    
    plt.title('Залежність завантаження ресурсів від часу моделювання', fontweight='bold')
    plt.xlabel('Час моделювання (хв)')
    plt.ylabel('Коефіцієнт завантаження')
    plt.ylim(0, 1.05)
    plt.legend(title='Ресурс:', loc='lower right')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig('utilization_run1.svg', format='svg')
    plt.close()

    # --- Графіки 3 і 4: Гістограми розподілів ---
    df_stable_wait = df_wait[df_wait['Time'] > 60000]

    def plot_distribution(data, title, filename):
        if len(data) == 0: return
        plt.figure(figsize=(10, 6))
        count, bins, _ = plt.hist(data, bins=60, density=True, alpha=0.6, color='skyblue', edgecolor='black', label='Емпіричні дані')
        
        mean_val = data.mean()
        if mean_val > 0:
            x = np.linspace(min(bins), max(bins), 1000)
            pdf = expon.pdf(x, scale=mean_val)
            plt.plot(x, pdf, 'r-', lw=2.5, label=f'Експоненціальний закон (λ={1/mean_val:.3f})')
            
        plt.title(title, fontweight='bold')
        plt.xlabel('Час очікування (хв)')
        plt.ylabel('Щільність імовірності')
        plt.legend(loc='upper right')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        plt.savefig(filename, format='svg')
        plt.close()

    wait_20t = df_stable_wait[df_stable_wait['TruckType'] == 20]['WaitTime'].values
    wait_50t = df_stable_wait[df_stable_wait['TruckType'] == 50]['WaitTime'].values

    plot_distribution(wait_20t, 'Розподіл часу очікування вантажівок 20т (низький пріоритет)', 'distribution_wait_20t.svg')
    plot_distribution(wait_50t, 'Розподіл часу очікування вантажівок 50т (високий пріоритет)', 'distribution_wait_50t.svg')

    # --- Перевірка Пірсона (Хі-Квадрат) ---
    print("\n--- Перевірка розподілу за критерієм Пірсона (Chi-squared) ---")
    def chi_squared_exponential_test(data, alpha=0.05):
        n = len(data)
        if n == 0: return False, 0, 0, 0
        mean = np.mean(data)
        
        bins = int(np.ceil(1 + 3.322 * np.log10(n))) 
        observed_counts, bin_edges = np.histogram(data, bins=bins)
        expected_counts = np.diff(n * (1 - np.exp(-bin_edges / mean)))
        
        valid_bins = expected_counts > 0
        observed_counts = observed_counts[valid_bins]
        expected_counts = expected_counts[valid_bins]
        
        chi_squared_stat = np.sum((observed_counts - expected_counts)**2 / expected_counts)
        degrees_of_freedom = len(observed_counts) - 1 - 1 
        
        if degrees_of_freedom <= 0: return False, 0, 0, 0
        
        critical_value = chi2.ppf(1 - alpha, degrees_of_freedom)
        p_value = 1 - chi2.cdf(chi_squared_stat, degrees_of_freedom)
        
        return chi_squared_stat < critical_value, p_value, chi_squared_stat, critical_value

    is_exp, p_val, chi_stat, crit_val = chi_squared_exponential_test(wait_50t)
    
    print(f"Аналіз часу очікування вантажівок 50т (Вибірка: {len(wait_50t)} подій)")
    print(f"Статистика Хі-квадрат: {chi_stat:.4f}")
    print(f"Критичне значення: {crit_val:.4f}")
    if is_exp:
        print("ВИСНОВОК: Гіпотеза про експоненціальний розподіл ПРИЙМАЄТЬСЯ.")
    else:
        print("ВИСНОВОК: Гіпотеза ВІДХИЛЯЄТЬСЯ (через пріоритет черга не є суто марковською).")
else:
    print(f"\nПомилка: Не знайдено папку {base_dir}. Переконайтеся, що Java код згенерував папки Set_0 ... Set_4.")


# =====================================================================
# ЧАСТИНА 3: ВИВІД ДЛЯ ДОДАТКУ А (ВЕЛИКІ ТАБЛИЦІ)
# =====================================================================
if not df_results.empty:
    print("\n" + "="*50)
    print("ДОДАТОК А\nРезультати верифікації")
    print("="*50)

    print("\nТаблиця А.1 Набори параметрів")
    print("| Індекс | Розвант. 20т | Розвант. 50т | Вантаж. 20т | Дод. 50т | Пріоритет 50т |")
    print("| :--- | :--- | :--- | :--- | :--- | :--- |")
    print("| 0 | 5.0 | 4.0 | 5.0 | 0 | 1 |")
    print("| 1 | 10.0 | 8.0 | 5.0 | 0 | 1 |")
    print("| 2 | 5.0 | 4.0 | 2.5 | 0 | 1 |")
    print("| 3 | 5.0 | 4.0 | 5.0 | 1 | 1 |")
    print("| 4 | 5.0 | 4.0 | 5.0 | 0 | 0 |")

    print("\nТаблиця А.2 Середні значення вихідних параметрів (по кожному прогону)")
    print("| Набір | Прогін | Завант. дробівки | Черга дробівки | Завант. екскаватора 1 |")
    print("| :--- | :--- | :--- | :--- | :--- |")
    for _, row in df_results.iterrows():
        print(f"| {int(row['Set'])} | {int(row['Run'])} | {row['Mean_Crush_Util']:.8f} | {row['Mean_Crush_Q']:.8f} | {row['Mean_Exc_Util']:.8f} |")

    print("\nТаблиця А.3 Середньоквадратичні відхилення (по кожному прогону)")
    print("| Набір | Прогін | Завант. дробівки | Черга дробівки | Завант. екскаватора 1 |")
    print("| :--- | :--- | :--- | :--- | :--- |")
    for _, row in df_results.iterrows():
        print(f"| {int(row['Set'])} | {int(row['Run'])} | {row['Std_Crush_Util']:.8f} | {row['Std_Crush_Q']:.8f} | {row['Std_Exc_Util']:.8f} |")

    print("\nТаблиця А.4 Глобальні середні значення (за 5 прогонами)")
    print("| Індекс набору | Завант. дробівки | Черга дробівки | Завант. екскаватора 1 |")
    print("| :--- | :--- | :--- | :--- |")
    for _, row in global_means.iterrows():
        print(f"| {int(row['Set'])} | {row['Mean_Crush_Util']:.8f} | {row['Mean_Crush_Q']:.8f} | {row['Mean_Exc_Util']:.8f} |")

    print("\nТаблиця А.6 Відсоткові відхилення середніх значень відносно глобальних середніх (%)")
    print("| Набір | Прогін | Завант. дробівки | Черга дробівки | Завант. екскаватора 1 |")
    print("| :--- | :--- | :--- | :--- | :--- |")
    for _, row in df_results.iterrows():
        set_idx = int(row['Set'])
        g_mean_crush = global_means.loc[global_means['Set'] == set_idx, 'Mean_Crush_Util'].values[0]
        g_mean_q = global_means.loc[global_means['Set'] == set_idx, 'Mean_Crush_Q'].values[0]
        g_mean_exc = global_means.loc[global_means['Set'] == set_idx, 'Mean_Exc_Util'].values[0]
        
        dev_crush = abs(row['Mean_Crush_Util'] - g_mean_crush) / g_mean_crush * 100 if g_mean_crush != 0 else 0
        dev_q = abs(row['Mean_Crush_Q'] - g_mean_q) / g_mean_q * 100 if g_mean_q != 0 else 0
        dev_exc = abs(row['Mean_Exc_Util'] - g_mean_exc) / g_mean_exc * 100 if g_mean_exc != 0 else 0
        
        print(f"| {set_idx} | {int(row['Run'])} | {dev_crush:.6f}% | {dev_q:.6f}% | {dev_exc:.6f}% |")
        
    print("\nГенерація завершена успішно!")