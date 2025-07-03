import yfinance as yf
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Set non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from datetime import datetime, timedelta
import pandas as pd
import os

# Download S&P 500 data with auto_adjust=True
sp500 = yf.download('^GSPC', start='2010-01-01', end=datetime.today().strftime('%Y-%m-%d'), auto_adjust=True)

# Calculate 12-month rolling returns
sp500['12_month_return'] = sp500['Close'].pct_change(periods=252)  # 252 trading days in a year

# Clean data - remove NaN values
returns = sp500['12_month_return'].dropna()

# Create a DataFrame of 12-month periods with dates and returns
periods_df = pd.DataFrame({
    'Start Date': sp500.index[:-252],  # Start date of each 12-month period
    'End Date': sp500.index[252:],     # End date (12 months later)
    'Return (%)': returns * 100        # Percentage return
})

# Save to CSV and get full path
csv_filename = 'sp500_12month_returns.csv'
periods_df.to_csv(csv_filename, index=False)
full_csv_path = os.path.abspath(csv_filename)

# Calculate key metrics
metrics = {
    'Mean Return (%)': returns.mean() * 100,
    'Median Return (%)': returns.median() * 100,
    'Standard Deviation (%)': returns.std() * 100,
    'Minimum Return (%)': returns.min() * 100,
    'Maximum Return (%)': returns.max() * 100,
    'Positive Periods (%)': (returns > 0).mean() * 100,
    'Negative Periods (%)': (returns < 0).mean() * 100
}

# Test for normality
shapiro_test = stats.shapiro(returns)
normality = {
    'Shapiro-Wilk Statistic': shapiro_test[0],
    'p-value': shapiro_test[1],
    'Normally Distributed?': 'Yes' if shapiro_test[1] > 0.05 else 'No'
}

# Plotting
plt.figure(figsize=(12, 7))
sns.histplot(returns * 100, bins=20, kde=True, color='royalblue', edgecolor='black')
plt.axvline(metrics['Mean Return (%)'], color='red', linestyle='--', label=f'Mean: {metrics["Mean Return (%)"]:.2f}%')
plt.axvline(metrics['Median Return (%)'], color='green', linestyle='--', label=f'Median: {metrics["Median Return (%)"]:.2f}%')
plt.title('Distribution of 12-Month S&P 500 Returns (2010-Present)', fontsize=16)
plt.xlabel('12-Month Return (%)', fontsize=14)
plt.ylabel('Frequency', fontsize=14)
plt.legend(fontsize=12)

# Add metrics text box
metrics_text = "\n".join([f"{k}: {v:.2f}" if isinstance(v, float) else f"{k}: {v}" 
                         for k, v in {**metrics, **normality}.items()])
plt.text(0.95, 0.95, metrics_text, transform=plt.gca().transAxes, 
         fontsize=10, verticalalignment='top', horizontalalignment='right',
         bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

plt.grid(True, alpha=0.3)
plt.tight_layout()

# Save the plot instead of showing it
plot_filename = 'sp500_returns_plot.png'
plt.savefig(plot_filename)
plt.close()

# Print output information
print(f"\nAnalysis complete! Files saved to:")
print(f"1. CSV of returns: {full_csv_path}")
print(f"2. Plot: {os.path.abspath(plot_filename)}\n")
print("Metrics Summary:")
for k, v in {**metrics, **normality}.items():
    print(f"{k}: {v:.2f}" if isinstance(v, float) else f"{k}: {v}")