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
# ЧАСТИНА 1: ЗБІР УСІЄЇ СТАТИСТИКИ
# =====================================================================
all_data = []

for set_idx in range(5):
    for run in range(1, 6):
        file_path = f"Set_{set_idx}/Run_{run}/simulation_stats.csv"
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            
            metric = df['Average Crusher Queue']
            final_value = metric.iloc[-1]
            epsilon = 0.02 * final_value if final_value > 0 else 0.02
            
            out_of_corridor = np.abs(metric - final_value) > epsilon
            indices = np.where(out_of_corridor)[0]
            
            t_transient = df.loc[indices[-1], 'Time'] if len(indices) > 0 else 0.0
            
            max_allowed_t = df['Time'].max() * 0.25
            if t_transient > max_allowed_t:
                t_transient = max_allowed_t
            
            df_stable = df[df['Time'] > t_transient]
            
            all_data.append({
                'Set': set_idx, 'Run': run,
                'Mean_Crush_Util': df_stable['Crusher Utilization'].mean(),
                'Mean_Crush_Q': df_stable['Average Crusher Queue'].mean(),
                'Mean_Exc1_Util': df_stable['Excavator 1 Utilization'].mean(),
                'Mean_Exc2_Util': df_stable['Excavator 2 Utilization'].mean(),
                'Mean_Exc3_Util': df_stable['Excavator 3 Utilization'].mean()
            })

df_results = pd.DataFrame(all_data)
global_means = df_results.groupby('Set').mean().reset_index()

# =====================================================================
# ЧАСТИНА 2: РОЗДІЛ 4 (ГРАФІКИ ТА АНАЛІЗ)
# =====================================================================
print("\n" + "="*95)
print(f"{'=== РОЗДІЛ 4: ЕКСПЕРИМЕНТАЛЬНЕ ДОСЛІДЖЕННЯ ===':^95}")
print("="*95)

if not global_means.empty:
    print("\nТаблиця 4.1 - Середні показники стаціонарного режиму для 5 сценаріїв:")
    h41 = f"| {'Сценарій (Set)':<25} | {'Зав.Дроб.':^10} | {'Черг.Дроб.':^10} | {'Зав.Ек1':^9} | {'Зав.Ек2':^9} | {'Зав.Ек3':^9} |"
    s41 = f"|{'-'*27}|{'-'*12}|{'-'*12}|{'-'*11}|{'-'*11}|{'-'*11}|"
    print(h41); print(s41)
    
    scenario_names = ["Set_0 (Базовий)", "Set_1 (Повільна др.)", "Set_2 (Швидкі екск.)", "Set_3 (Більше парк)", "Set_4 (Без пріор.)"]
    for idx, row in global_means.iterrows():
        print(f"| {scenario_names[int(row['Set'])]:<25} | {row['Mean_Crush_Util']:^10.4f} | {row['Mean_Crush_Q']:^10.4f} | {row['Mean_Exc1_Util']:^9.4f} | {row['Mean_Exc2_Util']:^9.4f} | {row['Mean_Exc3_Util']:^9.4f} |")

base_dir = "Set_0/Run_1"
if os.path.exists(f"{base_dir}/simulation_stats.csv"):
    df_stats = pd.read_csv(f"{base_dir}/simulation_stats.csv")
    df_wait = pd.read_csv(f"{base_dir}/wait_times.csv")
    
    # Розрахунок перехідного періоду Run 1
    metric_run1 = df_stats['Average Crusher Queue']
    final_val_run1 = metric_run1.iloc[-1]
    epsilon_run1 = 0.02 * final_val_run1 if final_val_run1 > 0 else 0.02
    unstable_points = df_stats.index[np.abs(metric_run1 - final_val_run1) > epsilon_run1].tolist()
    t_transient_run1 = df_stats.loc[unstable_points[-1], 'Time'] if len(unstable_points) > 0 else 0.0
    if t_transient_run1 > df_stats['Time'].max() * 0.20: t_transient_run1 = df_stats['Time'].max() * 0.20
    
    print(f"\n[*] Програмно розрахований час перехідного періоду для Run_1: T = {t_transient_run1:.2f} хв.")

    # Графік 1: Черги
    plt.figure(figsize=(10, 5))
    plt.plot(df_stats['Time'], df_stats['Average Crusher Queue'], color='red', linewidth=2.5, label='Дробівка')
    plt.plot(df_stats['Time'], df_stats['Excavator 1 Average Queue'], color='#1f77b4', linewidth=1.5, label='Екскаватор 1')
    plt.plot(df_stats['Time'], df_stats['Excavator 2 Average Queue'], color='#ff7f0e', linewidth=1.5, linestyle='--', label='Екскаватор 2')
    plt.plot(df_stats['Time'], df_stats['Excavator 3 Average Queue'], color='#2ca02c', linewidth=1.5, linestyle=':', label='Екскаватор 3')
    plt.axvline(x=t_transient_run1, color='black', linestyle='--', linewidth=1.5, label='Межа T_trans')
    plt.axvspan(0, t_transient_run1, color='gray', alpha=0.1)
    plt.title('Залежність середньої довжини черг від часу моделювання', fontweight='bold')
    plt.xlabel('Час (хв)'); plt.ylabel('Кількість вантажівок')
    plt.legend(loc='upper right'); plt.grid(True, linestyle='--', alpha=0.6); plt.tight_layout()
    plt.savefig('average_queues_run1.svg', format='svg'); plt.close()

    # Графік 2: Завантаження
    plt.figure(figsize=(10, 5))
    plt.plot(df_stats['Time'], df_stats['Crusher Utilization'], color='red', linewidth=2.5, label='Дробівка')
    plt.plot(df_stats['Time'], df_stats['Excavator 1 Utilization'], color='#1f77b4', linewidth=1.5, label='Екскаватор 1')
    plt.plot(df_stats['Time'], df_stats['Excavator 2 Utilization'], color='#ff7f0e', linewidth=1.5, linestyle='--', label='Екскаватор 2')
    plt.plot(df_stats['Time'], df_stats['Excavator 3 Utilization'], color='#2ca02c', linewidth=1.5, linestyle=':', label='Екскаватор 3')
    plt.axvline(x=t_transient_run1, color='black', linestyle='--', linewidth=1.5)
    plt.axvspan(0, t_transient_run1, color='gray', alpha=0.1)
    plt.title('Залежність завантаження ресурсів від часу моделювання', fontweight='bold')
    plt.xlabel('Час (хв)'); plt.ylabel('Коефіцієнт'); plt.ylim(0, 1.05)
    plt.legend(loc='lower right'); plt.grid(True, linestyle='--', alpha=0.6); plt.tight_layout()
    plt.savefig('utilization_run1.svg', format='svg'); plt.close()

    # Хі-квадрат
    print("\n--- Перевірка розподілу за критерієм Пірсона (Chi-squared) ---")
    df_stable_wait = df_wait[df_wait['Time'] > t_transient_run1]
    wait_50t = df_stable_wait[df_stable_wait['TruckType'] == 50]['WaitTime'].values
    
    def chi_squared_test(data):
        n = len(data)
        if n == 0: return False, 0, 0, 0
        mean = np.mean(data)
        bins = int(np.ceil(1 + 3.322 * np.log10(n))) 
        obs, edges = np.histogram(data, bins=bins)
        exp_counts = np.diff(n * (1 - np.exp(-edges / mean)))
        valid = exp_counts > 0
        chi_stat = np.sum((obs[valid] - exp_counts[valid])**2 / exp_counts[valid])
        df_val = len(obs[valid]) - 2
        crit = chi2.ppf(0.95, df_val)
        return chi_stat < crit, chi_stat, crit
    
    is_exp, chi_stat, crit_val = chi_squared_test(wait_50t)
    print(f"Аналіз вантажівок 50т (Вибірка: {len(wait_50t)} подій)")
    print(f"Статистика Хі-квадрат: {chi_stat:.4f}, Критичне: {crit_val:.4f}")
    print("ВИСНОВОК: Гіпотеза " + ("ПРИЙМАЄТЬСЯ." if is_exp else "ВІДХИЛЯЄТЬСЯ."))

# =====================================================================
# ЧАСТИНА 3: ДОДАТОК А
# =====================================================================
if not df_results.empty:
    print("\n" + "="*85)
    print(f"{'ДОДАТОК А':^85}\n{'Результати верифікації':^85}")
    print("="*85)

    # Таблиця А.2
    print("\nТаблиця А.2 Середні значення вихідних параметрів")
    h_a2 = f"| {'Набір':^5} | {'Пр':^3} | {'Зав.Дроб.':^10} | {'Черг.Дроб.':^10} | {'Зав.Ек1':^9} | {'Зав.Ек2':^9} | {'Зав.Ек3':^9} |"
    s_a2 = f"|{'-'*7}|{'-'*5}|{'-'*12}|{'-'*12}|{'-'*11}|{'-'*11}|{'-'*11}|"
    print(h_a2); print(s_a2)
    for _, row in df_results.iterrows():
        print(f"| {int(row['Set']):^5} | {int(row['Run']):^3} | {row['Mean_Crush_Util']:^10.5f} | {row['Mean_Crush_Q']:^10.5f} | {row['Mean_Exc1_Util']:^9.5f} | {row['Mean_Exc2_Util']:^9.5f} | {row['Mean_Exc3_Util']:^9.5f} |")

    # Таблиця А.4
    print("\nТаблиця А.4 Глобальні середні значення")
    h_a4 = f"| {'Набір':^5} | {'Зав.Дроб.':^10} | {'Черг.Дроб.':^10} | {'Зав.Ек1':^9} | {'Зав.Ек2':^9} | {'Зав.Ек3':^9} |"
    s_a4 = f"|{'-'*7}|{'-'*12}|{'-'*12}|{'-'*11}|{'-'*11}|{'-'*11}|"
    print(h_a4); print(s_a4)
    for _, row in global_means.iterrows():
        print(f"| {int(row['Set']):^5} | {row['Mean_Crush_Util']:^10.5f} | {row['Mean_Crush_Q']:^10.5f} | {row['Mean_Exc1_Util']:^9.5f} | {row['Mean_Exc2_Util']:^9.5f} | {row['Mean_Exc3_Util']:^9.5f} |")

    # Таблиця А.6 (ВИПРАВЛЕНО ВИРІВНЮВАННЯ %)
    print("\nТаблиця А.6 Відсоткові відхилення (%)")
    print(h_a2); print(s_a2)
    for _, row in df_results.iterrows():
        s = int(row['Set'])
        gm = global_means[global_means['Set'] == s].iloc[0]
        cols = ['Mean_Crush_Util', 'Mean_Crush_Q', 'Mean_Exc1_Util', 'Mean_Exc2_Util', 'Mean_Exc3_Util']
        devs = [abs(row[c] - gm[c])/gm[c]*100 if gm[c] != 0 else 0 for c in cols]
        
        # СТВОРЮЄМО РЯДКИ З % ВСЕРЕДИНІ ЦЕНТРУВАННЯ
        d0 = f"{devs[0]:.4f} %"; d1 = f"{devs[1]:.4f} %"
        d2 = f"{devs[2]:.4f} %"; d3 = f"{devs[3]:.4f} %"; d4 = f"{devs[4]:.4f} %"
        
        print(f"| {s:^5} | {int(row['Run']):^3} | {d0:^10} | {d1:^10} | {d2:^9} | {d3:^9} | {d4:^9} |")

print("\nГенерація завершена успішно!")