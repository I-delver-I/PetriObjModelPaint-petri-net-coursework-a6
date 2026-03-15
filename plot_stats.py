import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import expon, chi2
import matplotlib
import os
import warnings
from tabulate import tabulate

warnings.filterwarnings('ignore')

matplotlib.rcParams['font.family'] = 'Times New Roman'
matplotlib.rcParams['font.size'] = 12

print("ЗБІР ДАНИХ З УСІХ 25 ПРОГОНІВ...")

# =====================================================================
# ЧАСТИНА 1: ЗБІР УСІЄЇ СТАТИСТИКИ
# =====================================================================
all_data = []
for set_idx in range(5):
    for run in range(1, 6):
        file_path = f"Set_{set_idx}/Run_{run}/simulation_stats.csv"
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            
            # Використовуємо згладжену чергу для аналізу стабільності
            metric = df['Average Crusher Queue'].expanding().mean()
            final_value = metric.iloc[-1]
            epsilon = 0.02 * final_value if final_value > 0 else 0.02
            indices = np.where(np.abs(metric - final_value) > epsilon)[0]
            t_transient = df.loc[indices[-1], 'Time'] if len(indices) > 0 else 0.0
            
            max_allowed_t = df['Time'].max() * 0.25
            if t_transient > max_allowed_t: t_transient = max_allowed_t
            
            df_stable = df[df['Time'] > t_transient]
            
            all_data.append({
                'Set': set_idx, 'Run': run,
                'Mean_Crush_Util': df_stable['Crusher Utilization'].mean(),
                'Mean_Crush_Q': df_stable['Average Crusher Queue'].mean(),
                'Mean_Exc1_Util': df_stable['Excavator 1 Utilization'].mean(),
                'Mean_Exc2_Util': df_stable['Excavator 2 Utilization'].mean(),
                'Mean_Exc3_Util': df_stable['Excavator 3 Utilization'].mean(),
                'Std_Crush_Util': df_stable['Crusher Utilization'].std(),
                'Std_Crush_Q': df_stable['Average Crusher Queue'].std(),
                'Std_Exc1_Util': df_stable['Excavator 1 Utilization'].std(),
                'Std_Exc2_Util': df_stable['Excavator 2 Utilization'].std(),
                'Std_Exc3_Util': df_stable['Excavator 3 Utilization'].std()
            })

df_results = pd.DataFrame(all_data)

global_means = df_results.groupby('Set')[['Mean_Crush_Util', 'Mean_Crush_Q', 
                                          'Mean_Exc1_Util', 'Mean_Exc2_Util', 'Mean_Exc3_Util']].mean().reset_index()

global_stds = df_results.groupby('Set')[['Mean_Crush_Util', 'Mean_Crush_Q', 
                                         'Mean_Exc1_Util', 'Mean_Exc2_Util', 'Mean_Exc3_Util']].std().reset_index()


# =====================================================================
# ЧАСТИНА 2: РОЗДІЛ 4 (ГРАФІКИ ТА АНАЛІЗ)
# =====================================================================
print("\n" + "="*115)
print(f"{'=== РОЗДІЛ 4: ЕКСПЕРИМЕНТАЛЬНЕ ДОСЛІДЖЕННЯ ===':^115}")
print("="*115)

if not global_means.empty:
    print("\nТаблиця 4.1 - Середні показники стаціонарного режиму для 5 сценаріїв:")
    scenario_names = ["Set_0 (Базовий)", "Set_1 (Повільна др.)", "Set_2 (Швидкі екск.)", 
                      "Set_3 (Більше парк)", "Set_4 (Без пріор.)"]
    
    table_41 = []
    for idx, row in global_means.iterrows():
        table_41.append([
            scenario_names[int(row['Set'])],
            f"{row['Mean_Crush_Util']:.4f}", f"{row['Mean_Crush_Q']:.4f}",
            f"{row['Mean_Exc1_Util']:.4f}", f"{row['Mean_Exc2_Util']:.4f}", f"{row['Mean_Exc3_Util']:.4f}"
        ])
    
    headers_descriptive_set = ["Сценарій (Set)", "Завантаження Дробівки", "Черга до Дробівки", 
                               "Завант. Екскаватора 1", "Завант. Екскаватора 2", "Завант. Екскаватора 3"]
    print(tabulate(table_41, headers=headers_descriptive_set, tablefmt="github", stralign="center"))

base_dir = "Set_0/Run_1"
if os.path.exists(f"{base_dir}/simulation_stats.csv"):
    df_stats = pd.read_csv(f"{base_dir}/simulation_stats.csv")
    df_wait = pd.read_csv(f"{base_dir}/wait_times.csv")
    
    metric_run1 = df_stats['Average Crusher Queue'].expanding().mean()
    final_val_run1 = metric_run1.iloc[-1]
    epsilon_run1 = 0.02 * final_val_run1 if final_val_run1 > 0 else 0.02
    unstable_points = df_stats.index[np.abs(metric_run1 - final_val_run1) > epsilon_run1].tolist()
    t_trans_run1 = df_stats.loc[unstable_points[-1], 'Time'] if len(unstable_points) > 0 else 0.0
    if t_trans_run1 > df_stats['Time'].max() * 0.20: t_trans_run1 = df_stats['Time'].max() * 0.20
    
    print(f"\n[*] Програмно розрахований час перехідного періоду для Run_1: T = {t_trans_run1:.2f} хв.")

    plt.figure(figsize=(10, 5))
    plt.plot(df_stats['Time'], df_stats['Average Crusher Queue'].expanding().mean(), color='red', 
             linewidth=2.5, label='Дробівка')
    plt.plot(df_stats['Time'], df_stats['Excavator 1 Average Queue'].expanding().mean(), 
             color='#1f77b4', linewidth=1.5, label='Екскаватор 1')
    plt.plot(df_stats['Time'], df_stats['Excavator 2 Average Queue'].expanding().mean(), 
             color='#ff7f0e', linewidth=1.5, linestyle='--', label='Екскаватор 2')
    plt.plot(df_stats['Time'], df_stats['Excavator 3 Average Queue'].expanding().mean(), 
             color='#2ca02c', linewidth=1.5, linestyle=':', label='Екскаватор 3')
    plt.axvline(x=t_trans_run1, color='black', linestyle='--', linewidth=1.5, label='Межа T_trans')
    plt.axvspan(0, t_trans_run1, color='gray', alpha=0.1)
    plt.title('Залежність середньої довжини черг від часу моделювання', fontweight='bold')
    plt.xlabel('Час (хв)'); plt.ylabel('Середня кількість вантажівок')
    plt.legend(loc='upper right'); plt.grid(True, linestyle='--', alpha=0.6); plt.tight_layout()
    plt.savefig('average_queues_run1.svg', format='svg'); plt.close()

    plt.figure(figsize=(10, 5))
    plt.plot(df_stats['Time'], df_stats['Crusher Utilization'].expanding().mean(), color='red', 
             linewidth=2.5, label='Дробівка')
    plt.plot(df_stats['Time'], df_stats['Excavator 1 Utilization'].expanding().mean(), color='#1f77b4', 
             linewidth=1.5, label='Екскаватор 1')
    plt.plot(df_stats['Time'], df_stats['Excavator 2 Utilization'].expanding().mean(), color='#ff7f0e', 
             linewidth=1.5, linestyle='--', label='Екскаватор 2')
    plt.plot(df_stats['Time'], df_stats['Excavator 3 Utilization'].expanding().mean(), color='#2ca02c', 
             linewidth=1.5, linestyle=':', label='Екскаватор 3')
    plt.axvline(x=t_trans_run1, color='black', linestyle='--', linewidth=1.5, label='Межа T_trans')
    plt.axvspan(0, t_trans_run1, color='gray', alpha=0.1)
    plt.title('Залежність завантаження ресурсів від часу моделювання', fontweight='bold')
    plt.xlabel('Час (хв)'); plt.ylabel('Коефіцієнт завантаження'); plt.ylim(0, 1.05)
    plt.legend(loc='lower right'); plt.grid(True, linestyle='--', alpha=0.6); plt.tight_layout()
    plt.savefig('utilization_run1.svg', format='svg'); plt.close()

    print("\n--- Перевірка розподілу за критерієм Пірсона (Chi-squared) ---")
    df_stable_wait = df_wait[df_wait['Time'] > t_trans_run1]
    wait_50t = df_stable_wait[df_stable_wait['TruckType'] == 50]['WaitTime'].values
    
    def chi_squared_test(data):
        if len(data) == 0: return False, 0, 0
        n = len(data)
        mean = np.mean(data)
        bins = int(np.ceil(1 + 3.322 * np.log10(n))) 
        obs, edges = np.histogram(data, bins=bins)
        exp_counts = np.diff(n * (1 - np.exp(-edges / mean)))
        valid = exp_counts > 0
        chi_stat = np.sum((obs[valid] - exp_counts[valid])**2 / exp_counts[valid])
        df_val = len(obs[valid]) - 2
        if df_val <= 0: return False, 0, 0
        crit = chi2.ppf(0.95, df_val)
        return chi_stat < crit, chi_stat, crit
    
    is_exp, chi_stat, crit_val = chi_squared_test(wait_50t)
    print(f"Аналіз вантажівок 50т (Вибірка: {len(wait_50t)} подій)")
    print(f"Статистика Хі-квадрат: {chi_stat:.4f}, Критичне: {crit_val:.4f}")
    print("ВИСНОВОК: Гіпотеза " + ("ПРИЙМАЄТЬСЯ." if is_exp else "ВІДХИЛЯЄТЬСЯ."))
    
    wait_20t = df_stable_wait[df_stable_wait['TruckType'] == 20]['WaitTime'].values

    if len(wait_50t) > 0:
        plt.figure(figsize=(10, 5))
        count, bins, _ = plt.hist(wait_50t, bins=50, density=True, alpha=0.6, 
                                  color='lightblue', edgecolor='black', label='Емпіричні дані')
        
        mean_50t = np.mean(wait_50t)
        lambda_50t = 1.0 / mean_50t if mean_50t > 0 else 0
        x_50 = np.linspace(0, max(wait_50t), 1000)
        y_50 = lambda_50t * np.exp(-lambda_50t * x_50)
        
        plt.plot(x_50, y_50, 'r-', lw=2.5, label=f'Експоненціальний закон (λ={lambda_50t:.3f})')
        plt.title('Розподіл часу очікування вантажівок 50т (високий пріоритет)', fontweight='bold')
        plt.xlabel('Час очікування (хв)')
        plt.ylabel('Щільність імовірності')
        plt.legend(loc='upper right')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        plt.savefig('distribution_wait_50t.svg', format='svg')
        plt.close()

    if len(wait_20t) > 0:
        plt.figure(figsize=(10, 5))
        count, bins, _ = plt.hist(wait_20t, bins=50, density=True, alpha=0.6, color='lightblue', 
                                  edgecolor='black', label='Емпіричні дані')
        
        mean_20t = np.mean(wait_20t)
        lambda_20t = 1.0 / mean_20t if mean_20t > 0 else 0
        x_20 = np.linspace(0, max(wait_20t), 1000)
        y_20 = lambda_20t * np.exp(-lambda_20t * x_20)
        
        plt.plot(x_20, y_20, 'r-', lw=2.5, label=f'Експоненціальний закон (λ={lambda_20t:.3f})')
        plt.title('Розподіл часу очікування вантажівок 20т (низький пріоритет)', fontweight='bold')
        plt.xlabel('Час очікування (хв)')
        plt.ylabel('Щільність імовірності')
        plt.legend(loc='upper right')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        plt.savefig('distribution_wait_20t.svg', format='svg')
        plt.close()
        
    print("[*] Графіки розподілу (гістограми) успішно згенеровано та збережено!")

# =====================================================================
# ЧАСТИНА 3: ДОДАТОК А (ПОВНИЙ НАБІР ТАБЛИЦЬ)
# =====================================================================
if not df_results.empty:
    print("\n" + "="*115)
    print(f"{'ДОДАТОК А':^115}\n{'Результати верифікації':^115}")
    print("="*115)

    headers_descriptive_run = ["Набір", "Прогін", "Завантаження Дробівки", "Черга до Дробівки", 
                               "Завант. Екскаватора 1", "Завант. Екскаватора 2", "Завант. Екскаватора 3"]
    headers_descriptive_global = ["Набір", "Завантаження Дробівки", "Черга до Дробівки", 
                                  "Завант. Екскаватора 1", "Завант. Екскаватора 2", "Завант. Екскаватора 3"]

    print("\nТаблиця А.2 Середні значення вихідних параметрів")
    table_a2 = []
    for _, row in df_results.iterrows():
        table_a2.append([
            int(row['Set']), int(row['Run']),
            f"{row['Mean_Crush_Util']:.5f}", f"{row['Mean_Crush_Q']:.5f}",
            f"{row['Mean_Exc1_Util']:.5f}", f"{row['Mean_Exc2_Util']:.5f}", f"{row['Mean_Exc3_Util']:.5f}"
        ])
    print(tabulate(table_a2, headers=headers_descriptive_run, tablefmt="github", stralign="center"))

    print("\nТаблиця А.3 Середньоквадратичні відхилення вихідних параметрів")
    table_a3 = []
    for _, row in df_results.iterrows():
        table_a3.append([
            int(row['Set']), int(row['Run']),
            f"{row['Std_Crush_Util']:.5f}", f"{row['Std_Crush_Q']:.5f}",
            f"{row['Std_Exc1_Util']:.5f}", f"{row['Std_Exc2_Util']:.5f}", f"{row['Std_Exc3_Util']:.5f}"
        ])
    print(tabulate(table_a3, headers=headers_descriptive_run, tablefmt="github", stralign="center"))

    print("\nТаблиця А.4 Глобальні середні значення")
    table_a4 = []
    for _, row in global_means.iterrows():
        table_a4.append([
            int(row['Set']),
            f"{row['Mean_Crush_Util']:.5f}", f"{row['Mean_Crush_Q']:.5f}",
            f"{row['Mean_Exc1_Util']:.5f}", f"{row['Mean_Exc2_Util']:.5f}", f"{row['Mean_Exc3_Util']:.5f}"
        ])
    print(tabulate(table_a4, headers=headers_descriptive_global, tablefmt="github", stralign="center"))

    print("\nТаблиця А.5 Глобальні середньоквадратичні відхилення")
    table_a5 = []
    for _, row in global_stds.iterrows():
        table_a5.append([
            int(row['Set']),
            f"{row['Mean_Crush_Util']:.5f}", f"{row['Mean_Crush_Q']:.5f}",
            f"{row['Mean_Exc1_Util']:.5f}", f"{row['Mean_Exc2_Util']:.5f}", f"{row['Mean_Exc3_Util']:.5f}"
        ])
    print(tabulate(table_a5, headers=headers_descriptive_global, tablefmt="github", stralign="center"))

    print("\nТаблиця А.6 Відсоткові відхилення (%)")
    table_a6 = []
    for _, row in df_results.iterrows():
        s = int(row['Set'])
        gm = global_means[global_means['Set'] == s].iloc[0]
        cols = ['Mean_Crush_Util', 'Mean_Crush_Q', 'Mean_Exc1_Util', 'Mean_Exc2_Util', 'Mean_Exc3_Util']
        devs = [abs(row[c] - gm[c])/gm[c]*100 if gm[c] != 0 else 0 for c in cols]
        
        table_a6.append([
            s, int(row['Run']),
            f"{devs[0]:.4f} %", f"{devs[1]:.4f} %", f"{devs[2]:.4f} %", f"{devs[3]:.4f} %", f"{devs[4]:.4f} %"
        ])
    print(tabulate(table_a6, headers=headers_descriptive_run, tablefmt="github", stralign="center"))

print("\nГенерація завершена успішно!")