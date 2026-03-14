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
print("\n" + "="*50)
print("=== РОЗДІЛ 4: ЕКСПЕРИМЕНТАЛЬНЕ ДОСЛІДЖЕННЯ ===")
print("="*50)

if not global_means.empty:
    print("\nТаблиця 4.1 - Середні показники стаціонарного режиму для 5 сценаріїв:")
    print(f"{'Сценарій (Set)':<25} | {'Зав.Дроб.':<10} | {'Черг.Дроб.':<10} | {'Зав.Ек1':<8} | {'Зав.Ек2':<8} | {'Зав.Ек3':<8}")
    print("-" * 90)
    scenario_names = ["Set_0 (Базовий)", "Set_1 (Повільна дробівка)", "Set_2 (Швидкі екскаватори)", "Set_3 (Збільшення парку)", "Set_4 (Без пріоритету)"]
    for idx, row in global_means.iterrows():
        print(f"{scenario_names[int(row['Set'])]:<25} | {row['Mean_Crush_Util']:<10.4f} | {row['Mean_Crush_Q']:<10.4f} | {row['Mean_Exc1_Util']:<8.4f} | {row['Mean_Exc2_Util']:<8.4f} | {row['Mean_Exc3_Util']:<8.4f}")

base_dir = "Set_0/Run_1"
if os.path.exists(f"{base_dir}/simulation_stats.csv"):
    print(f"\n--- Побудова графіків для базового сценарію ({base_dir}) ---")
    df_stats = pd.read_csv(f"{base_dir}/simulation_stats.csv")
    df_wait = pd.read_csv(f"{base_dir}/wait_times.csv")
    
    # --- КРОК 1: СПОЧАТКУ розраховуємо t_transient_run1 ---
    metric_run1 = df_stats['Average Crusher Queue']
    final_val_run1 = metric_run1.iloc[-1]
    epsilon_run1 = 0.02 * final_val_run1 if final_val_run1 > 0 else 0.02
    unstable_points = df_stats.index[np.abs(metric_run1 - final_val_run1) > epsilon_run1].tolist()
    
    t_transient_run1 = df_stats.loc[unstable_points[-1], 'Time'] if len(unstable_points) > 0 else 0.0
    if t_transient_run1 > df_stats['Time'].max() * 0.20:
        t_transient_run1 = df_stats['Time'].max() * 0.20
    
    print(f"[*] Програмно розрахований час перехідного періоду для Run_1: T = {t_transient_run1:.2f} хв.")

    # --- КРОК 2: ТЕПЕР будуємо графіки (змінна вже визначена) ---
    
    # Графік 1: Динаміка черг
    plt.figure(figsize=(10, 5))
    plt.plot(df_stats['Time'], df_stats['Average Crusher Queue'], color='red', linewidth=2.5, label='Дробівка')
    plt.plot(df_stats['Time'], df_stats['Excavator 1 Average Queue'], color='#1f77b4', linewidth=1.5, label='Екскаватор 1')
    plt.plot(df_stats['Time'], df_stats['Excavator 2 Average Queue'], color='#ff7f0e', linewidth=1.5, linestyle='--', label='Екскаватор 2')
    plt.plot(df_stats['Time'], df_stats['Excavator 3 Average Queue'], color='#2ca02c', linewidth=1.5, linestyle=':', label='Екскаватор 3')
    
    # Маркування перехідного періоду
    plt.axvline(x=t_transient_run1, color='black', linestyle='--', linewidth=1.5, label=f'Межа T_trans')
    plt.axvspan(0, t_transient_run1, color='gray', alpha=0.1, label='Перехідний період')
    
    plt.title('Залежність середньої довжини черг від часу моделювання', fontweight='bold')
    plt.xlabel('Час моделювання (хв)'); plt.ylabel('Середня кількість вантажівок')
    plt.legend(title='Ресурс:', loc='upper right'); plt.grid(True, linestyle='--', alpha=0.6); plt.tight_layout()
    plt.savefig('average_queues_run1.svg', format='svg'); plt.close()

    # Графік 2: Динаміка завантаження
    plt.figure(figsize=(10, 5))
    plt.plot(df_stats['Time'], df_stats['Crusher Utilization'], color='red', linewidth=2.5, label='Дробівка')
    plt.plot(df_stats['Time'], df_stats['Excavator 1 Utilization'], color='#1f77b4', linewidth=1.5, label='Екскаватор 1')
    plt.plot(df_stats['Time'], df_stats['Excavator 2 Utilization'], color='#ff7f0e', linewidth=1.5, linestyle='--', label='Екскаватор 2')
    plt.plot(df_stats['Time'], df_stats['Excavator 3 Utilization'], color='#2ca02c', linewidth=1.5, linestyle=':', label='Екскаватор 3')
    
    # Маркування перехідного періоду
    plt.axvline(x=t_transient_run1, color='black', linestyle='--', linewidth=1.5)
    plt.axvspan(0, t_transient_run1, color='gray', alpha=0.1)
    
    plt.title('Залежність завантаження ресурсів від часу моделювання', fontweight='bold')
    plt.xlabel('Час моделювання (хв)'); plt.ylabel('Коефіцієнт завантаження'); plt.ylim(0, 1.05)
    plt.legend(title='Ресурс:', loc='lower right'); plt.grid(True, linestyle='--', alpha=0.6); plt.tight_layout()
    plt.savefig('utilization_run1.svg', format='svg'); plt.close()

    # --- КРОК 3: Гістограми та Хі-квадрат ---
    df_stable_wait = df_wait[df_wait['Time'] > t_transient_run1]

    def plot_distribution(data, title, filename):
        if len(data) == 0: return
        plt.figure(figsize=(10, 6))
        plt.hist(data, bins=60, density=True, alpha=0.6, color='skyblue', edgecolor='black', label='Емпіричні дані')
        mean_val = data.mean()
        if mean_val > 0:
            x = np.linspace(min(data), max(data), 1000)
            pdf = expon.pdf(x, scale=mean_val)
            plt.plot(x, pdf, 'r-', lw=2.5, label=f'Експоненціальний закон (λ={1/mean_val:.3f})')
        plt.title(title, fontweight='bold'); plt.xlabel('Час очікування (хв)'); plt.ylabel('Щільність імовірності')
        plt.legend(loc='upper right'); plt.grid(True, linestyle='--', alpha=0.6); plt.tight_layout()
        plt.savefig(filename, format='svg'); plt.close()

    wait_20t = df_stable_wait[df_stable_wait['TruckType'] == 20]['WaitTime'].values
    wait_50t = df_stable_wait[df_stable_wait['TruckType'] == 50]['WaitTime'].values
    plot_distribution(wait_20t, 'Розподіл часу очікування вантажівок 20т (низький пріоритет)', 'distribution_wait_20t.svg')
    plot_distribution(wait_50t, 'Розподіл часу очікування вантажівок 50т (високий пріоритет)', 'distribution_wait_50t.svg')

    print("\n--- Перевірка розподілу за критерієм Пірсона (Chi-squared) ---")
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
    print("\n" + "="*50 + "\nДОДАТОК А\nРезультати верифікації\n" + "="*50)
    print("\nТаблиця А.2 Середні значення вихідних параметрів")
    print("| Набір | Пр | Зав.Дроб. | Черг.Дроб. | Зав.Ек1 | Зав.Ек2 | Зав.Ек3 |")
    print("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for _, row in df_results.iterrows():
        print(f"| {int(row['Set'])} | {int(row['Run'])} | {row['Mean_Crush_Util']:.5f} | {row['Mean_Crush_Q']:.5f} | {row['Mean_Exc1_Util']:.5f} | {row['Mean_Exc2_Util']:.5f} | {row['Mean_Exc3_Util']:.5f} |")

    print("\nТаблиця А.4 Глобальні середні значення")
    print("| Набір | Зав.Дроб. | Черг.Дроб. | Зав.Ек1 | Зав.Ек2 | Зав.Ек3 |")
    print("| :--- | :--- | :--- | :--- | :--- | :--- |")
    for _, row in global_means.iterrows():
        print(f"| {int(row['Set'])} | {row['Mean_Crush_Util']:.5f} | {row['Mean_Crush_Q']:.5f} | {row['Mean_Exc1_Util']:.5f} | {row['Mean_Exc2_Util']:.5f} | {row['Mean_Exc3_Util']:.5f} |")

    print("\nТаблиця А.6 Відсоткові відхилення (%)")
    print("| Набір | Пр | Зав.Дроб. | Черг.Дроб. | Зав.Ек1 | Зав.Ек2 | Зав.Ек3 |")
    print("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for _, row in df_results.iterrows():
        s = int(row['Set'])
        gm = global_means[global_means['Set'] == s].iloc[0]
        # Динамічне обчислення відхилень для всіх 5 метрик
        cols = ['Mean_Crush_Util', 'Mean_Crush_Q', 'Mean_Exc1_Util', 'Mean_Exc2_Util', 'Mean_Exc3_Util']
        devs = [abs(row[c] - gm[c])/gm[c]*100 if gm[c] != 0 else 0 for c in cols]
        print(f"| {s} | {int(row['Run'])} | {devs[0]:.4f}% | {devs[1]:.4f}% | {devs[2]:.4f}% | {devs[3]:.4f}% | {devs[4]:.4f}% |")

print("\nГенерація завершена успішно!")