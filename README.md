# Portfolio Manager

## Overview

This Portfolio Manager is a software program designed to help manage and rebalance strategic investment portfolios. It can be used for:

1. Seeding an initial investment portfolio
2. Performing periodic maintenance of the portfolio, including replacing existing investments, adding new positions, or reducing existing positions

This is written with the help of AI. This is primarily a learning exercise to help me understand the capabilities of AI and how to use it to build software. The code is not perfect and is a work in progress.

## Setup

```
pyenv virtualenv 3.8.18 portfolio_manager
pyenv local portfolio_manager
pip install -r requirements.txt
```

## Inputs

The Portfolio Manager takes three input CSV files and a configuration YAML file:

1. `portfolio_weights.csv`: Contains the portfolio cash weights
2. `accounts.csv`: Contains the accounts in the portfolio
3. `current_allocations.csv`: Contains the current allocations
4. `config.yaml`: Contains the file paths for the input CSV files

### 1. Portfolio Weights (portfolio_weights.csv)

This file contains the following columns:

- Ticker
- Volatility
- Cash_Weight
- Asset_Class
- Sub_Class

Example:

```
Ticker,Vol,Cash_Weight,Asset_Class,Sub_Class
VWOB,0.0836,0.015,Bond,EM gov
CEMB,0.0457,0.028,Bond,EM corp
EMHY,0.0725,0.018,Bond,EM HY
VWO,0.1315,0.045,Equity,EM Beta
DEM,0.1292,0.088,Equity,EM HY
```

### 2. Accounts (accounts.csv)

This file contains the following columns:

- Account
- Type
- Idle_Cash

Example:

```
Account,Type,Idle_Cash
Taxable,Taxable,10000
IRA,Tax-Advantaged,5000
Solo401K,Tax-Advantaged,2000
```

### 3. Current Allocations (current_allocations.csv)

This file contains the following columns:

- Ticker
- Account
- Shares

Example:

```
Ticker,Account,Shares
VWOB,Taxable,10
DEM,Solo401K,10
SPY,Taxable,5
```

### 4. Configuration (config.yaml)

This YAML file specifies the paths to the input CSV files. The paths are relative to the directory location of the config.yaml file.

Example:

```yaml
portfolio_weights: ./portfolio_weights.csv
accounts: ./accounts.csv
current_allocations: ./current_allocations.csv
```

## Usage

To run the Portfolio Manager:

```
python portfolio_manager.py [path_to_config.yaml]
```

If no config file is specified, it defaults to `./config.yaml` in the current directory.

## Rebalancing Process

The Portfolio Manager follows these steps to rebalance the portfolio:

1. Read the input files specified in the config.yaml
2. Fetch current prices of investments from Yahoo Finance
3. Calculate the total portfolio value (including idle cash in each account)
4. Determine the target allocation for each investment based on the total portfolio value and cash weights
5. Adjust the current allocation to reach the target allocation, considering:
   - Volatile investments should be in tax-advantaged accounts
   - New investments are allocated based on volatility
   - Investments no longer in the portfolio weights are sold
   - Current allocations can be empty (new portfolio)
   - Investments may be split among several accounts if necessary

## Key Features

- Handles both new portfolio creation and existing portfolio rebalancing
- Prioritizes tax-efficient placement of investments
- Applies a 5% threshold for rebalancing to minimize unnecessary trades
- Handles adding new investments and removing old ones
- Can split investments across multiple accounts when necessary
- Sorts buy and sell orders by volatility and account type for optimal execution

## Testing

To run the unit tests:

```
python -m unittest test_portfolio_manager.py
```

The test suite includes various scenarios such as new portfolio creation, rebalancing existing portfolios, handling new investments, and edge cases like insufficient funds.

## Notes

- The Portfolio Manager uses the `yfinance` library to fetch current prices. Ensure you have an active internet connection when running the program.
- All calculations are performed using the `Decimal` type to ensure precision in financial calculations.
- The program uses logging to provide detailed information about the rebalancing process. You can adjust the logging level in the `portfolio_manager.py` file.
