import yfinance as yf
from decimal import Decimal, ROUND_DOWN
from collections import defaultdict
import logging
import yaml
import csv
import os
import sys

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class DataLoader:
    @staticmethod
    def load_from_config(config_path):
        logger.debug(f"Loading config from {config_path}")
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        base_dir = os.path.dirname(os.path.abspath(config_path))

        portfolio_data = {
            "portfolio_weights": DataLoader.load_csv(
                os.path.join(base_dir, config["portfolio_weights"])
            ),
            "accounts": DataLoader.load_csv(os.path.join(base_dir, config["accounts"])),
            "current_allocations": DataLoader.load_csv(
                os.path.join(base_dir, config["current_allocations"])
            ),
        }

        logger.debug(f"Loaded portfolio data: {portfolio_data}")
        return portfolio_data

    @staticmethod
    def load_from_data(portfolio_weights, accounts, current_allocations):
        return {
            "portfolio_weights": portfolio_weights,
            "accounts": accounts,
            "current_allocations": current_allocations,
        }

    @staticmethod
    def load_csv(file_path):
        logger.debug(f"Loading CSV from {file_path}")
        with open(file_path, "r") as f:
            reader = csv.DictReader(f)
            data = list(reader)
        logger.debug(f"Loaded {len(data)} rows from {file_path}")
        return data


class PortfolioManager:
    def __init__(self, portfolio_data):
        self.prices = {}
        self.portfolio_weights = {
            pw["Ticker"]: pw for pw in portfolio_data["portfolio_weights"]
        }
        self.accounts = {a["Account"]: a for a in portfolio_data["accounts"]}
        self.current_allocations = portfolio_data["current_allocations"]

    def get_price(self, ticker):
        if ticker not in self.prices:
            self.prices[ticker] = Decimal(
                str(yf.Ticker(ticker).info["regularMarketPrice"])
            )
        return self.prices[ticker]

    def rebalance(self):
        logger.debug("Starting rebalance...")
        self.calculate_current_state()
        self.calculate_target_state()
        self.apply_rebalance_threshold()

        sell_orders = self.generate_sell_orders()
        self.execute_sell_orders(sell_orders)
        buy_orders = self.generate_buy_orders()

        all_orders = sell_orders + buy_orders
        logger.debug(f"All orders before combining: {all_orders}")
        combined_orders = self.combine_orders(all_orders)
        logger.debug(f"Final orders: {combined_orders}")
        return combined_orders

    def calculate_current_state(self):
        logger.debug("Calculating current state...")
        self.current_state = defaultdict(lambda: defaultdict(Decimal))
        self.account_cash = {
            a["Account"]: Decimal(a["Idle_Cash"]) for a in self.accounts.values()
        }
        self.total_value = sum(self.account_cash.values())

        for allocation in self.current_allocations:
            ticker = allocation["Ticker"]
            account = allocation["Account"]
            shares = Decimal(allocation["Shares"])
            value = shares * self.get_price(ticker)
            self.current_state[ticker][account] = shares
            self.total_value += value

        logger.debug(f"Current state: {dict(self.current_state)}")
        logger.debug(f"Account cash: {self.account_cash}")
        logger.debug(f"Total value: {self.total_value}")

    def calculate_target_state(self):
        logger.debug("Calculating target state...")
        self.target_state = {}
        for ticker, weight in self.portfolio_weights.items():
            target_value = Decimal(weight["Cash_Weight"]) * self.total_value
            self.target_state[ticker] = (
                target_value / self.get_price(ticker)
            ).to_integral_value(rounding=ROUND_DOWN)
        logger.debug(f"Target state: {self.target_state}")

    def apply_rebalance_threshold(self):
        logger.debug("Applying 5% rebalance threshold...")
        for ticker, target_shares in self.target_state.items():
            current_shares = sum(self.current_state[ticker].values())
            current_value = current_shares * self.get_price(ticker)
            target_value = target_shares * self.get_price(ticker)

            if current_value == 0:
                # This is a new investment, don't apply threshold
                logger.debug(f"{ticker}: New investment. Target: {target_shares}")
                continue

            if abs(current_value - target_value) / current_value < Decimal("0.05"):
                logger.debug(
                    f"{ticker}: Within 5% threshold. Current: {current_shares}, Target: {target_shares}"
                )
                self.target_state[ticker] = current_shares
            else:
                logger.debug(
                    f"{ticker}: Outside 5% threshold. Current: {current_shares}, Target: {target_shares}"
                )

    def generate_sell_orders(self):
        logger.debug("Generating sell orders...")
        sell_orders = []

        # Sell investments no longer in portfolio weights
        for ticker in self.current_state:
            if ticker not in self.portfolio_weights:
                current_shares = sum(self.current_state[ticker].values())
                self.allocate_sell_orders(ticker, current_shares, sell_orders)

        # Sell excess shares of remaining investments
        for ticker, weight in self.portfolio_weights.items():
            target_shares = self.target_state[ticker]
            current_shares = sum(self.current_state[ticker].values())
            if current_shares > target_shares:
                self.allocate_sell_orders(
                    ticker, current_shares - target_shares, sell_orders
                )

        return sell_orders

    def execute_sell_orders(self, sell_orders):
        logger.debug("Executing sell orders...")
        for order in sell_orders:
            ticker = order["Ticker"]
            account = order["Account"]
            shares = order["Shares"]
            price = self.get_price(ticker)
            proceeds = shares * price
            self.account_cash[account] += proceeds
            self.current_state[ticker][account] -= shares
            logger.debug(
                f"Sold {shares} shares of {ticker} from {account}, added {proceeds} to cash"
            )

    def generate_buy_orders(self):
        logger.debug("Generating buy orders...")
        buy_orders = []
        for ticker, weight in sorted(
            self.portfolio_weights.items(),
            key=lambda x: Decimal(x[1]["Vol"]),
            reverse=True,
        ):
            target_shares = self.target_state[ticker]
            current_shares = sum(self.current_state[ticker].values())
            if target_shares > current_shares:
                self.allocate_buy_orders(
                    ticker, target_shares - current_shares, buy_orders
                )
        return buy_orders

    def allocate_sell_orders(self, ticker, shares_to_sell, orders):
        logger.debug(
            f"Allocating sell orders for {ticker}, shares to sell: {shares_to_sell}"
        )
        # Sort accounts to prioritize tax-advantaged accounts for selling
        sorted_accounts = sorted(
            self.accounts.items(),
            key=lambda x: (x[1]["Type"] != "Tax-Advantaged", x[0]),
        )

        for account_name, account in sorted_accounts:
            current_shares = self.current_state[ticker].get(account_name, 0)
            sellable_shares = min(shares_to_sell, current_shares)

            if sellable_shares >= 1:
                orders.append(
                    {
                        "Ticker": ticker,
                        "Account": account_name,
                        "Shares": int(sellable_shares),
                        "Action": "sell",
                    }
                )
                shares_to_sell -= sellable_shares
                logger.debug(
                    f"Allocated sell order: {sellable_shares} shares of {ticker} from {account_name}"
                )

            if shares_to_sell < 1:
                break

        if shares_to_sell >= 1:
            logger.warning(
                f"Unable to sell all shares for {ticker}. Remaining: {shares_to_sell}"
            )

    def allocate_buy_orders(self, ticker, shares_to_buy, orders):
        logger.debug(
            f"Allocating buy orders for {ticker}, shares to buy: {shares_to_buy}"
        )
        sorted_accounts = sorted(
            self.accounts.values(),
            key=lambda a: (
                a["Type"] == "Taxable",
                -Decimal(self.account_cash[a["Account"]]),
            ),
        )
        price = self.get_price(ticker)

        for account in sorted_accounts:
            account_name = account["Account"]
            available_cash = Decimal(self.account_cash[account_name])
            buyable_shares = min(
                shares_to_buy,
                (available_cash / price).to_integral_value(rounding=ROUND_DOWN),
            )

            if buyable_shares >= 1:
                orders.append(
                    {
                        "Ticker": ticker,
                        "Account": account_name,
                        "Shares": int(buyable_shares),
                        "Action": "buy",
                    }
                )
                self.account_cash[account_name] -= buyable_shares * price
                shares_to_buy -= buyable_shares
                logger.debug(
                    f"Bought {int(buyable_shares)} shares of {ticker} in {account_name}"
                )

            if shares_to_buy < 1:
                break

        if shares_to_buy >= 1:
            logger.warning(
                f"Unable to allocate all shares for {ticker}. Remaining: {shares_to_buy}"
            )

    def combine_orders(self, orders):
        logger.debug("Combining orders...")
        logger.debug(f"Initial orders: {orders}")

        sell_orders = []
        buy_orders = []

        for order in orders:
            if order["Action"] == "sell":
                sell_orders.append(order)
            else:
                buy_orders.append(order)

        # Sort sell orders
        sell_orders = sorted(
            sell_orders,
            key=lambda x: (
                -Decimal(
                    self.portfolio_weights.get(x["Ticker"], {"Vol": "0"})["Vol"]
                ),  # Sort by volatility (descending)
                x["Ticker"],  # Then by ticker
                self.accounts[x["Account"]]["Type"]
                == "Taxable",  # Tax-advantaged accounts first for same ticker
                x["Account"],  # Then by account name
            ),
        )

        # Sort buy orders
        buy_orders = sorted(
            buy_orders,
            key=lambda x: (
                -Decimal(
                    self.portfolio_weights[x["Ticker"]]["Vol"]
                ),  # Sort by volatility (descending)
                x["Ticker"],  # Then by ticker
                self.accounts[x["Account"]]["Type"]
                == "Taxable",  # Tax-advantaged accounts first for same ticker
                x["Account"],  # Then by account name
            ),
        )

        combined_orders = sell_orders + buy_orders

        logger.debug(f"Combined and sorted orders: {combined_orders}")
        return combined_orders


class PortfolioManagerFactory:
    @staticmethod
    def create_from_config(config_path):
        data = DataLoader.load_from_config(config_path)
        return PortfolioManager(data)

    @staticmethod
    def create_from_data(portfolio_weights, accounts, current_allocations):
        data = DataLoader.load_from_data(
            portfolio_weights, accounts, current_allocations
        )
        return PortfolioManager(data)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = "./config.yaml"

    manager = PortfolioManagerFactory.create_from_config(config_path)
    rebalance_orders = manager.rebalance()
    print("Rebalance orders:")
    for order in rebalance_orders:
        print(
            f"{order['Action']} {order['Shares']} shares of {order['Ticker']} in {order['Account']}"
        )
