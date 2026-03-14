import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import expon
import matplotlib

# --- 1. Налаштування шрифтів (Академічний стиль) ---
matplotlib.rcParams['font.family'] = 'Times New Roman'
matplotlib.rcParams['font.size'] = 12

# --- 2. Завантаження даних ---
# Перевірка наявності файлів перед початком
try:
    df_stats = pd.read_csv('simulation_stats.csv')
    df_wait = pd.read_csv('wait_times.csv')
except FileNotFoundError as e:
    print(f"Помилка: Файл {e.filename} не знайдено. Переконайтеся, що симуляція в Java була запущена.")
    exit()

# --- ЧАСТИНА А: Динаміка характеристик (Перехідний період) ---

# Графік середніх черг
plt.figure(figsize=(10, 5))
plt.plot(df_stats['Time'], df_stats['Average Crusher Queue'], color='#d62728', linewidth=2.5, label='Дробівка')
# Ефект вкладених ліній для візуалізації накладання екскаваторів
plt.plot(df_stats['Time'], df_stats['Excavator 1 Average Queue'], color='#1f77b4', linewidth=4, alpha=0.4, label='Екскаватор 1')
plt.plot(df_stats['Time'], df_stats['Excavator 2 Average Queue'], color='#ff7f0e', linewidth=2, alpha=0.8, linestyle='--', label='Екскаватор 2')
plt.plot(df_stats['Time'], df_stats['Excavator 3 Average Queue'], color='#2ca02c', linewidth=1, linestyle=':', label='Екскаватор 3')

plt.title('Залежність середньої довжини черг від часу моделювання', fontweight='bold')
plt.xlabel('Час моделювання (хв)')
plt.ylabel('Середня кількість вантажівок')
plt.legend(title='Ресурс:', loc='upper right')
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.savefig(fname='average_queues_dynamics.svg', format='svg')
plt.show()

# Графік коефіцієнтів завантаження
plt.figure(figsize=(10, 5))
plt.plot(df_stats['Time'], df_stats['Crusher Utilization'], color='#d62728', linewidth=2.5, label='Дробівка')
# Ефект вкладених ліній
plt.plot(df_stats['Time'], df_stats['Excavator 1 Utilization'], color='#1f77b4', linewidth=4, alpha=0.4, label='Екскаватор 1')
plt.plot(df_stats['Time'], df_stats['Excavator 2 Utilization'], color='#ff7f0e', linewidth=2, alpha=0.8, linestyle='--', label='Екскаватор 2')
plt.plot(df_stats['Time'], df_stats['Excavator 3 Utilization'], color='#2ca02c', linewidth=1, linestyle=':', label='Екскаватор 3')

plt.title('Залежність завантаження ресурсів від часу моделювання', fontweight='bold')
plt.xlabel('Час моделювання (хв)')
plt.ylabel('Коефіцієнт завантаження')
plt.ylim(0, 1.05)
plt.legend(title='Ресурс:', loc='lower right')
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.savefig(fname='utilization_dynamics.svg', format='svg')
plt.show()


# --- ЧАСТИНА Б: Аналіз розподілів (Стаціонарний режим) ---

# Виділення стабільного стану (T > 60,000 одиниць часу)
df_stable = df_wait[df_wait['Time'] > 60000]

def plot_distribution(data, title, filename):
    if data.empty:
        return
    plt.figure(figsize=(10, 6))
    # Гістограма
    count, bins, _ = plt.hist(data, bins=60, density=True, alpha=0.6, 
                              color='skyblue', edgecolor='black', label='Емпіричні дані')
    
    # Теоретична крива розподілу (Експоненціальний)
    mean_val = data.mean()
    x = np.linspace(min(bins), max(bins), 1000)
    pdf = expon.pdf(x, scale=mean_val)
    
    plt.plot(x, pdf, 'r-', lw=2.5, label=f'Експоненціальний закон (λ={1/mean_val:.3f})')
    plt.title(title, fontweight='bold')
    plt.xlabel('Час очікування (хв)')
    plt.ylabel('Щільність імовірності')
    plt.legend(loc='upper right')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(fname=filename, format='svg')
    plt.show()

# Розподіл для вантажівок 20т (Низький пріоритет)
wait_20t = df_stable[df_stable['TruckType'] == 20]['WaitTime']
plot_distribution(wait_20t, 'Розподіл часу очікування вантажівок 20т (низький пріоритет)', 'distribution_wait_20t.svg')

# Розподіл для вантажівок 50т (Високий пріоритет)
wait_50t = df_stable[df_stable['TruckType'] == 50]['WaitTime']
plot_distribution(wait_50t, 'Розподіл часу очікування вантажівок 50т (високий пріоритет)', 'distribution_wait_50t.svg')

print("\nГенерація завершена. Створено файли:")
print("- average_queues_dynamics.svg")
print("- utilization_dynamics.svg")
print("- distribution_wait_20t.svg")
print("- distribution_wait_50t.svg")