import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pypfopt import EfficientFrontier, risk_models, expected_returns
from pypfopt.discrete_allocation import DiscreteAllocation, get_latest_prices

# Configuration
START_DATE = '2010-01-01'
END_DATE = pd.Timestamp.today().strftime('%Y-%m-%d')
CASH = 100000  # Portfolio size in dollars
SPY = 'SPY'  # S&P 500 benchmark

def get_assets():
    """Select diverse assets with high liquidity and growth potential"""
    return [
        'SPY',  # S&P 500
        'QQQ',  # Nasdaq 100
        'DIA',  # Dow Jones
        'IWM',  # Russell 2000
        'VGK',  # Europe
        'EWJ',  # Japan
        'EEM',  # Emerging Markets
        'GLD',  # Gold
        'TLT',  # 20+ Year Treasuries
        'IEF',  # 7-10 Year Treasuries
        'DBC',  # Commodities
        'VNQ',  # Real Estate
        'XLE',  # Energy
        'XLF',  # Financials
        'XLK',  # Technology
        'XLV',  # Healthcare
        'XLI',  # Industrials
        'XLP',  # Consumer Staples
        'XLY',  # Consumer Discretionary
        'XLU',  # Utilities
    ]

def download_data(tickers):
    """Download adjusted close prices with caching"""
    data = yf.download(tickers, start=START_DATE, end=END_DATE, group_by='ticker', progress=False)
    prices = pd.DataFrame({ticker: data[ticker]['Adj Close'] for ticker in tickers})
    return prices.dropna()

def calculate_momentum(prices):
    """Calculate momentum scores (6m and 12m returns)"""
    momentum = pd.DataFrame()
    momentum['6m'] = prices.pct_change(126)  # 6 months
    momentum['12m'] = prices.pct_change(252)  # 12 months
    momentum['total'] = momentum['6m'] * 0.4 + momentum['12m'] * 0.6  # Weighted score
    return momentum

def optimize_portfolio(prices, momentum):
    """Create optimized portfolio using Modern Portfolio Theory"""
    # Select top 30% of assets by momentum
    selected = momentum.nlargest(int(len(momentum.columns)*0.3), 'total').columns
    
    # Calculate expected returns and covariance matrix
    mu = expected_returns.capm_return(prices[selected])
    S = risk_models.CovarianceShrinkage(prices[selected]).ledoit_wolf()
    
    # Optimize for maximum Sharpe ratio
    ef = EfficientFrontier(mu, S)
    ef.max_sharpe()
    weights = ef.clean_weights()
    
    return weights

def backtest_strategy(prices, weights, rebalance_freq='Q'):
    """Backtest the strategy against SPY"""
    # Create portfolio
    portfolio = pd.DataFrame(index=prices.index)
    portfolio['SPY'] = prices[SPY].pct_change()
    
    # Calculate portfolio returns
    for ticker, weight in weights.items():
        portfolio[ticker] = prices[ticker].pct_change() * weight
    
    portfolio['Strategy'] = portfolio.drop(columns=['SPY']).sum(axis=1)
    
    # Rebalance quarterly
    rebalance_dates = pd.date_range(start=prices.index[0], end=prices.index[-1], freq=rebalance_freq)
    for date in rebalance_dates:
        if date in portfolio.index:
            portfolio.loc[date:, 'Strategy'] = portfolio.loc[date:, [t for t in weights]].sum(axis=1)
    
    # Calculate cumulative returns
    cum_returns = (1 + portfolio[['SPY', 'Strategy']]).cumprod()
    
    return cum_returns

def plot_results(cum_returns):
    """Plot performance vs benchmark"""
    plt.figure(figsize=(12, 6))
    plt.plot(cum_returns['SPY'], label='S&P 500')
    plt.plot(cum_returns['Strategy'], label='Optimized Portfolio')
    plt.title('Portfolio Performance vs S&P 500')
    plt.xlabel('Date')
    plt.ylabel('Growth of $1')
    plt.legend()
    plt.grid(True)
    plt.show()

def generate_report(cum_returns):
    """Generate performance metrics report"""
    returns = cum_returns.pct_change().dropna()
    report = pd.DataFrame()
    
    report['Annual Return'] = returns.mean() * 252
    report['Annual Volatility'] = returns.std() * np.sqrt(252)
    report['Sharpe Ratio'] = report['Annual Return'] / report['Annual Volatility']
    report['Max Drawdown'] = (cum_returns / cum_returns.cummax() - 1).min()
    report['CAGR'] = (cum_returns.iloc[-1] ** (1/(len(cum_returns)/252))) - 1
    
    print("Performance Metrics:")
    print(report.round(3))
    
    print("\nStrategy Outperformance:", 
          f"{(cum_returns['Strategy'].iloc[-1]/cum_returns['SPY'].iloc[-1]-1)*100:.1f}%")

def main():
    # Get data and calculate momentum
    tickers = get_assets()
    prices = download_data(tickers)
    momentum = calculate_momentum(prices.iloc[-1:]).T  # Latest momentum
    
    # Optimize portfolio
    weights = optimize_portfolio(prices, momentum)
    print("Optimal Weights:")
    for ticker, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
        if weight > 0.01:  # Ignore weights < 1%
            print(f"{ticker}: {weight*100:.1f}%")
    
    # Backtest and show results
    cum_returns = backtest_strategy(prices, weights)
    plot_results(cum_returns)
    generate_report(cum_returns)
    
    # Generate discrete allocation
    latest_prices = get_latest_prices(prices)
    da = DiscreteAllocation(weights, latest_prices, total_portfolio_value=CASH)
    allocation, leftover = da.lp_portfolio()
    print(f"\nDiscrete Allocation (${CASH:,}):")
    for ticker, shares in allocation.items():
        print(f"{ticker}: {shares} shares (${latest_prices[ticker]*shares:,.0f})")
    print(f"Leftover: ${leftover:,.2f}")

if __name__ == '__main__':
    main()