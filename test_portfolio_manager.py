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
            {"Ticker": "VXUS", "Account": "IRA", "Shares": 600, "Action": "buy"},
            {"Ticker": "VTI", "Account": "401k", "Shares": 200, "Action": "buy"},
            {"Ticker": "VTI", "Account": "Taxable", "Shares": 200, "Action": "buy"},
            {"Ticker": "BNDX", "Account": "Taxable", "Shares": 111, "Action": "buy"},
            {"Ticker": "BND", "Account": "Taxable", "Shares": 250, "Action": "buy"},
        ]

        self.assertEqual(len(result), len(expected_allocations))
        for expected, actual in zip(expected_allocations, result):
            self.assertEqual(expected, actual)

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
            # 100 * 100 = 10000
            {"Ticker": "VTI", "Account": "Taxable", "Shares": "100"},
            # 50 * 50 = 2500
            {"Ticker": "VXUS", "Account": "IRA", "Shares": "50"},
            # 200 * 80 = 16000
            {"Ticker": "BND", "Account": "Taxable", "Shares": "200"},
        ]

        # total value = 5000 + 3000 + 10000 + 2500 + 16000 = 36500

        # target allocation
        #
        # VXUS = 0.35 * 36500 / 50 = 255
        # VTI = 0.45 * 36500 / 100 = 164
        # BND = 0.2 * 36500 / 80 = 91

        result = self.manager.rebalance(
            portfolio_weights, accounts, current_allocations
        )

        expected_allocations = [
            {"Ticker": "BND", "Account": "Taxable", "Shares": 109, "Action": "sell"},
            {"Ticker": "VXUS", "Account": "IRA", "Shares": 60, "Action": "buy"},
            {"Ticker": "VXUS", "Account": "Taxable", "Shares": 145, "Action": "buy"},
            {"Ticker": "VTI", "Account": "Taxable", "Shares": 64, "Action": "buy"},
        ]

        self.assertEqual(len(result), len(expected_allocations))
        for expected, actual in zip(expected_allocations, result):
            self.assertEqual(expected, actual)

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
            # VTI: 50 * 100 = 5000
            {"Ticker": "VTI", "Account": "Taxable", "Shares": "50"},
            # VXUS: 30 * 50 = 1500
            {"Ticker": "VXUS", "Account": "Taxable", "Shares": "30"},
            # BND: 100 * 80 = 8000
            {"Ticker": "BND", "Account": "Taxable", "Shares": "100"},
        ]

        # total value = 5000 + 1500 + 8000 + 1000 = 15500

        # target allocation:
        #
        # VTI: 15500 * 0.6 / 100 = 93
        # BND: 15500 * 0.4 / 80 = 77

        result = self.manager.rebalance(
            portfolio_weights, accounts, current_allocations
        )

        expected_allocations = [
            {"Ticker": "BND", "Account": "Taxable", "Shares": 23, "Action": "sell"},
            {"Ticker": "VXUS", "Account": "Taxable", "Shares": 30, "Action": "sell"},
            {"Ticker": "VTI", "Account": "Taxable", "Shares": 43, "Action": "buy"},
        ]

        self.assertEqual(len(result), len(expected_allocations))
        for expected, actual in zip(expected_allocations, result):
            self.assertEqual(expected, actual)

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
            # VTI: 50 * 100 = 5000
            {"Ticker": "VTI", "Account": "Taxable", "Shares": "50"},
            # VXUS: 40 * 50 = 2000
            {"Ticker": "VXUS", "Account": "IRA", "Shares": "40"},
            # BND: 100 * 80 = 8000
            {"Ticker": "BND", "Account": "Taxable", "Shares": "100"},
        ]

        # total value = 5000 + 2000 + 8000 + 10000 + 5000 = 30000

        # target allocation:
        #
        # VTI: 30000 * 0.4 / 100 = 120
        # VXUS: 30000 * 0.3 / 50 = 180
        # BND: 30000 * 0.2 / 80 = 75
        # GLD: 30000 * 0.1 / 150 = 20

        result = self.manager.rebalance(
            portfolio_weights, accounts, current_allocations
        )

        expected_allocations = [
            {"Ticker": "BND", "Account": "Taxable", "Shares": 25, "Action": "sell"},
            {"Ticker": "GLD", "Account": "IRA", "Shares": 20, "Action": "buy"},
            {"Ticker": "VXUS", "Account": "IRA", "Shares": 40, "Action": "buy"},
            {"Ticker": "VXUS", "Account": "Taxable", "Shares": 100, "Action": "buy"},
            {"Ticker": "VTI", "Account": "Taxable", "Shares": 70, "Action": "buy"},
        ]

        self.assertEqual(len(result), len(expected_allocations))
        for expected, actual in zip(expected_allocations, result):
            self.assertEqual(expected, actual)

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

        # total value = 50000 + 50000 = 100000

        # target allocation:
        #
        # VTI: 100000 * 0.3 / 100 = 300
        # ARKK: 100000 * 0.1 / 75 = 133
        # BND: 100000 * 0.6 / 80 = 750

        result = self.manager.rebalance(
            portfolio_weights, accounts, current_allocations
        )

        expected_allocations = [
            {"Ticker": "ARKK", "Account": "IRA", "Shares": 133, "Action": "buy"},
            {"Ticker": "VTI", "Account": "IRA", "Shares": 300, "Action": "buy"},
            {"Ticker": "BND", "Account": "IRA", "Shares": 125, "Action": "buy"},
            {"Ticker": "BND", "Account": "Taxable", "Shares": 625, "Action": "buy"},
        ]

        self.assertEqual(len(result), len(expected_allocations))
        for expected, actual in zip(expected_allocations, result):
            self.assertEqual(expected, actual)

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

        # total value = 60000 + 40000 = 100000

        # target allocation:
        #
        # VTI: 100000 * 0.8 / 100 = 800
        # BND: 100000 * 0.2 / 80 = 250

        result = self.manager.rebalance(
            portfolio_weights, accounts, current_allocations
        )

        expected_allocations = [
            {"Ticker": "VTI", "Account": "IRA", "Shares": 400, "Action": "buy"},
            {"Ticker": "VTI", "Account": "Taxable", "Shares": 400, "Action": "buy"},
            {"Ticker": "BND", "Account": "Taxable", "Shares": 250, "Action": "buy"},
        ]

        self.assertEqual(len(result), len(expected_allocations))
        for expected, actual in zip(expected_allocations, result):
            self.assertEqual(expected, actual)

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

        self.assertEqual(len(result), len(expected_allocations))
        for expected, actual in zip(expected_allocations, result):
            self.assertEqual(expected, actual)

    def test_prioritize_tax_advantaged_selling(self):
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
                "Cash_Weight": "0.3",
                "Asset_Class": "Bond",
                "Sub_Class": "US",
            },
        ]
        accounts = [
            {"Account": "Taxable", "Type": "Taxable", "Idle_Cash": "1000"},
            {"Account": "IRA", "Type": "Tax-Advantaged", "Idle_Cash": "1000"},
        ]
        current_allocations = [
            {"Ticker": "VTI", "Account": "Taxable", "Shares": "300"},
            {"Ticker": "VTI", "Account": "IRA", "Shares": "200"},
            {"Ticker": "VXUS", "Account": "IRA", "Shares": "100"},
            {"Ticker": "BND", "Account": "Taxable", "Shares": "50"},
        ]

        # Calculate total portfolio value:
        # VTI: (300 + 200) * 100 = 50,000
        # VXUS: 100 * 50 = 5,000
        # BND: 50 * 80 = 4,000
        # Idle cash: 1000 + 1000 = 2,000
        # Total: 61,000

        # Target allocation:
        # VTI: 61,000 * 0.4 / 100 = 244 shares
        # VXUS: 61,000 * 0.3 / 50 = 366 shares
        # BND: 61,000 * 0.3 / 80 = 228.75 shares (round down to 228)

        result = self.manager.rebalance(
            portfolio_weights, accounts, current_allocations
        )

        expected_allocations = [
            {"Ticker": "VTI", "Account": "IRA", "Shares": 200, "Action": "sell"},
            {"Ticker": "VTI", "Account": "Taxable", "Shares": 56, "Action": "sell"},
            {"Ticker": "VXUS", "Account": "IRA", "Shares": 266, "Action": "buy"},
            {"Ticker": "BND", "Account": "IRA", "Shares": 96, "Action": "buy"},
            {"Ticker": "BND", "Account": "Taxable", "Shares": 82, "Action": "buy"},
        ]

        self.assertEqual(len(result), len(expected_allocations))
        for expected, actual in zip(expected_allocations, result):
            self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
