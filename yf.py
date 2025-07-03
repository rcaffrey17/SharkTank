import yfinance as yf
import pandas as pd

# Download DXY data (max available history)
dxy = yf.download("DX-Y.NYB", start="2010-01-01", end="2025-01-01")

# Calculate 6-month returns (≈126 trading days)
dxy['6m_close_pct_change'] = dxy['Close'].pct_change(periods=126) * 100
dxy['6m_open_price'] = dxy['Open'].shift(126)  # Open price 6 months prior
dxy['6m_close_price'] = dxy['Close'].shift(126)  # Close price 6 months prior (for reference)

# Filter for drops >7%
big_drops = dxy[dxy['6m_close_pct_change'] < -7].dropna()

# Format output to show key details
result = big_drops[[
    'Open', 'Close', 
    '6m_open_price', '6m_close_price', 
    '6m_close_pct_change'
]].rename(columns={
    'Open': 'Current_Open',
    'Close': 'Current_Close',
    '6m_open_price': 'Open_6_Months_Ago',
    '6m_close_price': 'Close_6_Months_Ago',
    '6m_close_pct_change': '6m_%_Drop'
})

# Print results
print(f"Found {len(result)} 6-month periods with >7% drops:")
print(result[['Open_6_Months_Ago', 'Current_Close', '6m_%_Drop']].sort_values('6m_%_Drop'))

# Optional: Export to CSV
# Add this to your script (if not already present)
result.to_csv('dxy_6mo_drops_over_7pct.csv', index=True)

# Print all rows (no truncation)
pd.set_option('display.max_rows', None)
print(result)
