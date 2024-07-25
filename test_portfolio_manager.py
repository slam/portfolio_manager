import unittest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from portfolio_manager import PortfolioManager


class TestPortfolioManager(unittest.TestCase):
    def setUp(self):
        self.mock_prices = {
            "VTI": Decimal("100.00"),
            "VXUS": Decimal("50.00"),
            "BND": Decimal("80.00"),
            "BNDX": Decimal("90.00"),
            "ARKK": Decimal("75.00"),
            "GLD": Decimal("150.00"),
        }

        self.patcher = patch("portfolio_manager.yf.Ticker")
        self.mock_ticker = self.patcher.start()
        self.mock_ticker.side_effect = lambda symbol: MagicMock(
            info={"regularMarketPrice": self.mock_prices[symbol]}
        )

        self.manager = PortfolioManager()

    def tearDown(self):
        self.patcher.stop()

    def test_new_portfolio_creation(self):
        portfolio_weights = [
            {
                "Ticker": "VTI",
                "Vol": "0.1",
                "Cash_Weight": "0.4",
                "Asset_Class": "Equity",
                "Sub_Class": "US",
            },
            {
                "Ticker": "VXUS",
                "Vol": "0.12",
                "Cash_Weight": "0.3",
                "Asset_Class": "Equity",
                "Sub_Class": "International",
            },
            {
                "Ticker": "BND",
                "Vol": "0.03",
                "Cash_Weight": "0.2",
                "Asset_Class": "Bond",
                "Sub_Class": "US",
            },
            {
                "Ticker": "BNDX",
                "Vol": "0.04",
                "Cash_Weight": "0.1",
                "Asset_Class": "Bond",
                "Sub_Class": "International",
            },
        ]
        accounts = [
            {"Account": "Taxable", "Type": "Taxable", "Idle_Cash": "50000"},
            {"Account": "IRA", "Type": "Tax-Advantaged", "Idle_Cash": "30000"},
            {"Account": "401k", "Type": "Tax-Advantaged", "Idle_Cash": "20000"},
        ]
        current_allocations = []

        result = self.manager.rebalance(
            portfolio_weights, accounts, current_allocations
        )

        expected_allocations = [
            {"Ticker": "VTI", "Account": "Taxable", "Shares": 400, "Action": "buy"},
            {"Ticker": "VXUS", "Account": "IRA", "Shares": 600, "Action": "buy"},
            {"Ticker": "BND", "Account": "Taxable", "Shares": 250, "Action": "buy"},
            {"Ticker": "BNDX", "Account": "401k", "Shares": 111, "Action": "buy"},
        ]

        self.assertEqual(len(result), 4)
        for expected, actual in zip(expected_allocations, result):
            self.assertEqual(expected["Ticker"], actual["Ticker"])
            self.assertEqual(expected["Account"], actual["Account"])
            self.assertEqual(expected["Shares"], actual["Shares"])
            self.assertEqual(expected["Action"], actual["Action"])

    def test_portfolio_rebalancing(self):
        portfolio_weights = [
            {
                "Ticker": "VTI",
                "Vol": "0.1",
                "Cash_Weight": "0.45",
                "Asset_Class": "Equity",
                "Sub_Class": "US",
            },
            {
                "Ticker": "VXUS",
                "Vol": "0.12",
                "Cash_Weight": "0.35",
                "Asset_Class": "Equity",
                "Sub_Class": "International",
            },
            {
                "Ticker": "BND",
                "Vol": "0.03",
                "Cash_Weight": "0.2",
                "Asset_Class": "Bond",
                "Sub_Class": "US",
            },
        ]
        accounts = [
            {"Account": "Taxable", "Type": "Taxable", "Idle_Cash": "5000"},
            {"Account": "IRA", "Type": "Tax-Advantaged", "Idle_Cash": "3000"},
        ]
        current_allocations = [
            {"Ticker": "VTI", "Account": "Taxable", "Shares": "100"},
            {"Ticker": "VXUS", "Account": "IRA", "Shares": "50"},
            {"Ticker": "BND", "Account": "Taxable", "Shares": "200"},
        ]

        result = self.manager.rebalance(
            portfolio_weights, accounts, current_allocations
        )

        expected_allocations = [
            {"Ticker": "VTI", "Account": "Taxable", "Shares": 19, "Action": "buy"},
            {"Ticker": "VXUS", "Account": "IRA", "Shares": 106, "Action": "buy"},
            {"Ticker": "BND", "Account": "Taxable", "Shares": 95, "Action": "sell"},
        ]

        self.assertEqual(len(result), 3)
        for expected, actual in zip(expected_allocations, result):
            self.assertEqual(expected["Ticker"], actual["Ticker"])
            self.assertEqual(expected["Account"], actual["Account"])
            self.assertEqual(expected["Shares"], actual["Shares"])
            self.assertEqual(expected["Action"], actual["Action"])

    def test_removing_investment(self):
        portfolio_weights = [
            {
                "Ticker": "VTI",
                "Vol": "0.1",
                "Cash_Weight": "0.6",
                "Asset_Class": "Equity",
                "Sub_Class": "US",
            },
            {
                "Ticker": "BND",
                "Vol": "0.03",
                "Cash_Weight": "0.4",
                "Asset_Class": "Bond",
                "Sub_Class": "US",
            },
        ]
        accounts = [{"Account": "Taxable", "Type": "Taxable", "Idle_Cash": "1000"}]
        current_allocations = [
            {"Ticker": "VTI", "Account": "Taxable", "Shares": "50"},
            {"Ticker": "VXUS", "Account": "Taxable", "Shares": "30"},
            {"Ticker": "BND", "Account": "Taxable", "Shares": "100"},
        ]

        result = self.manager.rebalance(
            portfolio_weights, accounts, current_allocations
        )

        expected_allocations = [
            {"Ticker": "VTI", "Account": "Taxable", "Shares": 15, "Action": "buy"},
            {"Ticker": "VXUS", "Account": "Taxable", "Shares": 30, "Action": "sell"},
            {"Ticker": "BND", "Account": "Taxable", "Shares": 50, "Action": "sell"},
        ]

        self.assertEqual(len(result), 3)
        for expected, actual in zip(expected_allocations, result):
            self.assertEqual(expected["Ticker"], actual["Ticker"])
            self.assertEqual(expected["Account"], actual["Account"])
            self.assertEqual(expected["Shares"], actual["Shares"])
            self.assertEqual(expected["Action"], actual["Action"])

    def test_adding_new_investment(self):
        portfolio_weights = [
            {
                "Ticker": "VTI",
                "Vol": "0.1",
                "Cash_Weight": "0.4",
                "Asset_Class": "Equity",
                "Sub_Class": "US",
            },
            {
                "Ticker": "VXUS",
                "Vol": "0.12",
                "Cash_Weight": "0.3",
                "Asset_Class": "Equity",
                "Sub_Class": "International",
            },
            {
                "Ticker": "BND",
                "Vol": "0.03",
                "Cash_Weight": "0.2",
                "Asset_Class": "Bond",
                "Sub_Class": "US",
            },
            {
                "Ticker": "GLD",
                "Vol": "0.15",
                "Cash_Weight": "0.1",
                "Asset_Class": "Commodity",
                "Sub_Class": "Gold",
            },
        ]
        accounts = [
            {"Account": "Taxable", "Type": "Taxable", "Idle_Cash": "10000"},
            {"Account": "IRA", "Type": "Tax-Advantaged", "Idle_Cash": "5000"},
        ]
        current_allocations = [
            {"Ticker": "VTI", "Account": "Taxable", "Shares": "50"},
            {"Ticker": "VXUS", "Account": "IRA", "Shares": "40"},
            {"Ticker": "BND", "Account": "Taxable", "Shares": "100"},
        ]

        result = self.manager.rebalance(
            portfolio_weights, accounts, current_allocations
        )

        expected_allocations = [
            {"Ticker": "VTI", "Account": "Taxable", "Shares": 30, "Action": "buy"},
            {"Ticker": "VXUS", "Account": "IRA", "Shares": 140, "Action": "buy"},
            {"Ticker": "BND", "Account": "Taxable", "Shares": 25, "Action": "sell"},
            {"Ticker": "GLD", "Account": "IRA", "Shares": 13, "Action": "buy"},
        ]

        self.assertEqual(len(result), 4)
        for expected, actual in zip(expected_allocations, result):
            self.assertEqual(expected["Ticker"], actual["Ticker"])
            self.assertEqual(expected["Account"], actual["Account"])
            self.assertEqual(expected["Shares"], actual["Shares"])
            self.assertEqual(expected["Action"], actual["Action"])

    def test_volatility_and_account_types(self):
        portfolio_weights = [
            {
                "Ticker": "VTI",
                "Vol": "0.1",
                "Cash_Weight": "0.3",
                "Asset_Class": "Equity",
                "Sub_Class": "US",
            },
            {
                "Ticker": "ARKK",
                "Vol": "0.4",
                "Cash_Weight": "0.1",
                "Asset_Class": "Equity",
                "Sub_Class": "Tech",
            },
            {
                "Ticker": "BND",
                "Vol": "0.03",
                "Cash_Weight": "0.6",
                "Asset_Class": "Bond",
                "Sub_Class": "US",
            },
        ]
        accounts = [
            {"Account": "Taxable", "Type": "Taxable", "Idle_Cash": "50000"},
            {"Account": "IRA", "Type": "Tax-Advantaged", "Idle_Cash": "50000"},
        ]
        current_allocations = []

        result = self.manager.rebalance(
            portfolio_weights, accounts, current_allocations
        )

        expected_allocations = [
            {"Ticker": "VTI", "Account": "Taxable", "Shares": 300, "Action": "buy"},
            {"Ticker": "ARKK", "Account": "IRA", "Shares": 133, "Action": "buy"},
            {"Ticker": "BND", "Account": "Taxable", "Shares": 750, "Action": "buy"},
        ]

        self.assertEqual(len(result), 3)
        for expected, actual in zip(expected_allocations, result):
            self.assertEqual(expected["Ticker"], actual["Ticker"])
            self.assertEqual(expected["Account"], actual["Account"])
            self.assertEqual(expected["Shares"], actual["Shares"])
            self.assertEqual(expected["Action"], actual["Action"])

    def test_splitting_investments_across_accounts(self):
        portfolio_weights = [
            {
                "Ticker": "VTI",
                "Vol": "0.1",
                "Cash_Weight": "0.8",
                "Asset_Class": "Equity",
                "Sub_Class": "US",
            },
            {
                "Ticker": "BND",
                "Vol": "0.03",
                "Cash_Weight": "0.2",
                "Asset_Class": "Bond",
                "Sub_Class": "US",
            },
        ]
        accounts = [
            {"Account": "Taxable", "Type": "Taxable", "Idle_Cash": "60000"},
            {"Account": "IRA", "Type": "Tax-Advantaged", "Idle_Cash": "40000"},
        ]
        current_allocations = []

        result = self.manager.rebalance(
            portfolio_weights, accounts, current_allocations
        )

        expected_allocations = [
            {"Ticker": "VTI", "Account": "Taxable", "Shares": 480, "Action": "buy"},
            {"Ticker": "VTI", "Account": "IRA", "Shares": 320, "Action": "buy"},
            {"Ticker": "BND", "Account": "Taxable", "Shares": 250, "Action": "buy"},
        ]

        self.assertEqual(len(result), 3)
        for expected, actual in zip(expected_allocations, result):
            self.assertEqual(expected["Ticker"], actual["Ticker"])
            self.assertEqual(expected["Account"], actual["Account"])
            self.assertEqual(expected["Shares"], actual["Shares"])
            self.assertEqual(expected["Action"], actual["Action"])

    def test_handling_idle_cash(self):
        portfolio_weights = [
            {
                "Ticker": "VTI",
                "Vol": "0.1",
                "Cash_Weight": "1.0",
                "Asset_Class": "Equity",
                "Sub_Class": "US",
            }
        ]
        accounts = [{"Account": "Taxable", "Type": "Taxable", "Idle_Cash": "10000"}]
        current_allocations = []

        result = self.manager.rebalance(
            portfolio_weights, accounts, current_allocations
        )

        expected_allocations = [
            {"Ticker": "VTI", "Account": "Taxable", "Shares": 100, "Action": "buy"}
        ]

        self.assertEqual(len(result), 1)
        self.assertEqual(expected_allocations[0]["Ticker"], result[0]["Ticker"])
        self.assertEqual(expected_allocations[0]["Account"], result[0]["Account"])
        self.assertEqual(expected_allocations[0]["Shares"], result[0]["Shares"])
        self.assertEqual(expected_allocations[0]["Action"], result[0]["Action"])


if __name__ == "__main__":
    unittest.main()
