# Portfolio Manager


## Setup

```
pyenv virtualenv 3.8.18 portfolio_manager
pyenv local portfolio_manager
pip install -r requirements.txt
```

## Inputs

To rebalance, we need to have the following inputs:

List of Accounts in `accounts.csv`.

```
Account,Type,Cash_Flow
Etrade Taxable,Taxable,10000
Schwab IRA,Tax-Advantaged,5000
Carry Solo401K,Tax-Advantaged,2000
Schwab Taxable,Taxable,8000
```

List of ETFs and their cash weights and volatilities in `etf_weights.csv`.

```
Ticker,Vol,Cash_Weight,Asset_Class,Sub_Class
VWOB,0.0836,0.015,Bond,EM gov
CEMB,0.0457,0.028,Bond,EM corp
EMHY,0.0725,0.018,Bond,EM HY
BWX,0.0893,0.012,Bond,Non-US Gov
IBND,0.0855,0.012,Bond,Non-US Corp
HYXU,0.0812,0.017,Bond,Non-US HY
GOVT,0.0596,0.015,Bond,US Gov
LQD,0.0870,0.010,Bond,US Corp
JNK,0.0574,0.022,Bond,US HY
VWO,0.1315,0.045,Equity,EM Beta
DEM,0.1292,0.088,Equity,EM HY
EEMV,0.0908,0.097,Equity,EM Value
VPL,0.1306,0.029,Equity,Asia Beta
DVYA,0.1320,0.074,Equity,Asia HY
VGK,0.1289,0.036,Equity,Euro Beta
FDD,0.1392,0.070,Equity,Euro HY
EFV,0.1191,0.149,Equity,DM Value
VOO,0.1124,0.053,Equity,US Beta
VYM,0.1020,0.113,Equity,US HY
VTV,0.0983,0.099,Equity,US Value
```

Current Allocation in `current_allocation.csv`.

```
Ticker,Account,Current_Shares
VWOB,Etrade Taxable,1000
DEM,Carry Solo401K,100
```

## Rebalance

```
python portfolio_manager.py
```
