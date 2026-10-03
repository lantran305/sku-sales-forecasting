import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import random
import calendar

def plot_daily_qty_for_month(data, month):

    data_month = data[data['month'] == month].copy()

    data_month['day'] = data_month['shipped_date'].dt.day

    list_sku_random = random.sample(data_month['sku'].unique().tolist(), 5)
    data_plot = data_month[data_month['sku'].isin(list_sku_random)]


    grouped = (data_plot.groupby(['sku', 'day'])['qty'].sum().reset_index())


    fig, ax = plt.subplots(figsize=(14, 6))
    for sku in sorted(grouped['sku'].unique()):
        sku_data = grouped[grouped['sku'] == sku]
        ax.plot(
            sku_data['day'],
            sku_data['qty'],
            marker='o',
            label=f'SKU {sku}'
        )

    ax.set_title(f'Daily Quantity - {calendar.month_name[month]}')
    ax.set_xlabel('Day of Month')
    ax.set_ylabel('Quantity')
    ax.grid(True)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout()
    # plt.close(fig)
    # plt.show()
