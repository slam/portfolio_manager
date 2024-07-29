import unittest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from portfolio_manager import PortfolioManagerFactory


class TestPortfolioManager(unittest.TestCase):
    def setUp(self):
        self.default_prices = {
            "VTI": Decimal("100.00"),
            "VXUS": Decimal("50.00"),
            "BND": Decimal("80.00"),
            "BNDX": Decimal("90.00"),
            "ARKK": Decimal("75.00"),
            "GLD": Decimal("150.00"),
        }

        self.setup_price_mock(self.default_prices)

    def setup_price_mock(self, prices):
        patcher = patch("yfinance.Tickers")
        self.mock_tickers = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_tickers.return_value.tickers = {
            ticker: MagicMock(info={"previousClose": float(price)})
            for ticker, price in prices.items()
        }

    def test_file_based_initialization(self):
        with patch("portfolio_manager.DataLoader.load_from_config") as mock_load:
            mock_load.return_value = {
                "portfolio_weights": [
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
                ],
                "accounts": [
                    {"Account": "Taxable", "Type": "Taxable", "Idle_Cash": "10000"},
                    {"Account": "IRA", "Type": "Tax-Advantaged", "Idle_Cash": "5000"},
                ],
                "current_allocations": [
                    {"Ticker": "VTI", "Account": "Taxable", "Shares": "50"}
                ],
            }

            manager = PortfolioManagerFactory.create_from_config("dummy_config.yaml")

            self.assertEqual(len(manager.portfolio_weights), 2)
            self.assertEqual(manager.portfolio_weights["VTI"]["Cash_Weight"], "0.6")
            self.assertEqual(manager.portfolio_weights["BND"]["Cash_Weight"], "0.4")
            self.assertEqual(len(manager.accounts), 2)
            self.assertEqual(manager.accounts["Taxable"]["Idle_Cash"], "10000")
            self.assertEqual(manager.accounts["IRA"]["Idle_Cash"], "5000")
            self.assertEqual(len(manager.current_allocations), 1)
            self.assertEqual(manager.current_allocations[0]["Ticker"], "VTI")
            self.assertEqual(manager.current_allocations[0]["Shares"], "50")

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

        manager = PortfolioManagerFactory.create_from_data(
            portfolio_weights, accounts, current_allocations
        )
        result = manager.rebalance()

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

        manager = PortfolioManagerFactory.create_from_data(
            portfolio_weights, accounts, current_allocations
        )
        result = manager.rebalance()

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

        manager = PortfolioManagerFactory.create_from_data(
            portfolio_weights, accounts, current_allocations
        )
        result = manager.rebalance()

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

        manager = PortfolioManagerFactory.create_from_data(
            portfolio_weights, accounts, current_allocations
        )
        result = manager.rebalance()

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

        manager = PortfolioManagerFactory.create_from_data(
            portfolio_weights, accounts, current_allocations
        )
        result = manager.rebalance()

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

        manager = PortfolioManagerFactory.create_from_data(
            portfolio_weights, accounts, current_allocations
        )
        result = manager.rebalance()

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

        manager = PortfolioManagerFactory.create_from_data(
            portfolio_weights, accounts, current_allocations
        )
        result = manager.rebalance()

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

        manager = PortfolioManagerFactory.create_from_data(
            portfolio_weights, accounts, current_allocations
        )
        result = manager.rebalance()

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

    def test_no_rebalancing_needed_under_threshold(self):
        portfolio_weights = [
            {
                "Ticker": "VTI",
                "Vol": "0.1",
                "Cash_Weight": "0.6",
                "Asset_Class": "Equity",
                "Sub_Class": "US",
            },
            {
                "Ticker": "VXUS",
                "Vol": "0.12",
                "Cash_Weight": "0.4",
                "Asset_Class": "Equity",
                "Sub_Class": "International",
            },
        ]
        accounts = [
            {"Account": "Taxable", "Type": "Taxable", "Idle_Cash": "400"},
        ]
        current_allocations = [
            {"Ticker": "VTI", "Account": "Taxable", "Shares": "60"},
            {"Ticker": "VXUS", "Account": "Taxable", "Shares": "80"},
        ]

        test_prices = {
            "VTI": Decimal("100"),
            "VXUS": Decimal("50"),
        }
        self.setup_price_mock(test_prices)

        # total portfolio value = 1000 + 60 * 100 + 80 * 50 = 10000

        # target allocation:
        # VTI: 10400 * 0.6 / 100 = 62 shares < 5%
        # VXUS: 10400 * 0.4 / 50 = 83 shares < 5%
        #
        # No rebalancing needed

        manager = PortfolioManagerFactory.create_from_data(
            portfolio_weights, accounts, current_allocations
        )
        result = manager.rebalance()

        # Expected: No orders should be generated
        expected_allocations = []

        self.assertEqual(result, expected_allocations)

    def test_partial_rebalancing_minimize_costs(self):
        portfolio_weights = [
            {
                "Ticker": "VTI",
                "Vol": "0.1",
                "Cash_Weight": "0.5",
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
                "Vol": "0.05",
                "Cash_Weight": "0.2",
                "Asset_Class": "Bond",
                "Sub_Class": "US",
            },
        ]
        accounts = [
            {"Account": "Taxable", "Type": "Taxable", "Idle_Cash": "1000"},
        ]
        current_allocations = [
            {"Ticker": "VTI", "Account": "Taxable", "Shares": "50"},
            {"Ticker": "VXUS", "Account": "Taxable", "Shares": "60"},
            {"Ticker": "BND", "Account": "Taxable", "Shares": "10"},
        ]

        test_prices = {
            "VTI": Decimal("100"),
            "VXUS": Decimal("50"),
            "BND": Decimal("100"),
        }
        self.setup_price_mock(test_prices)

        # Total portfolio value = 1000 + 50*100 + 60*50 + 10*100 = 10000
        # Target allocation:
        # VTI: 10000 * 0.5 / 100 = 50 shares (no change, within 5%)
        # VXUS: 10000 * 0.3 / 50 = 60 shares (no change, within 5%)
        # BND: 10000 * 0.2 / 100 = 20 shares (100% increase, needs rebalancing)

        manager = PortfolioManagerFactory.create_from_data(
            portfolio_weights, accounts, current_allocations
        )
        result = manager.rebalance()

        # Expected: Only BND should be rebalanced
        expected_allocations = [
            {"Ticker": "BND", "Account": "Taxable", "Shares": 10, "Action": "buy"},
        ]

        self.assertEqual(result, expected_allocations)

    def test_full_rebalancing_minimize_costs(self):
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
                "Cash_Weight": "0.4",
                "Asset_Class": "Equity",
                "Sub_Class": "International",
            },
            {
                "Ticker": "BND",
                "Vol": "0.05",
                "Cash_Weight": "0.2",
                "Asset_Class": "Bond",
                "Sub_Class": "US",
            },
        ]
        accounts = [
            {"Account": "Taxable", "Type": "Taxable", "Idle_Cash": "1000"},
        ]
        current_allocations = [
            {"Ticker": "VTI", "Account": "Taxable", "Shares": "60"},
            {"Ticker": "VXUS", "Account": "Taxable", "Shares": "40"},
            {"Ticker": "BND", "Account": "Taxable", "Shares": "10"},
        ]

        test_prices = {
            "VTI": Decimal("100"),
            "VXUS": Decimal("100"),
            "BND": Decimal("100"),
        }
        self.setup_price_mock(test_prices)

        # Total portfolio value = 1000 + 60*100 + 40*100 + 10*100 = 12000
        # Target allocation:
        # VTI: 12000 * 0.4 / 100 = 48 shares (20% decrease, needs rebalancing)
        # VXUS: 12000 * 0.4 / 100 = 48 shares (20% increase, needs rebalancing)
        # BND: 12000 * 0.2 / 100 = 24 shares (140% increase, needs rebalancing)

        manager = PortfolioManagerFactory.create_from_data(
            portfolio_weights, accounts, current_allocations
        )
        result = manager.rebalance()

        # Expected: All positions should be rebalanced
        expected_allocations = [
            {"Ticker": "VTI", "Account": "Taxable", "Shares": 12, "Action": "sell"},
            {"Ticker": "VXUS", "Account": "Taxable", "Shares": 8, "Action": "buy"},
            {"Ticker": "BND", "Account": "Taxable", "Shares": 14, "Action": "buy"},
        ]

        self.assertEqual(result, expected_allocations)

    def test_edge_case_minimize_costs_threshold(self):
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
                "Vol": "0.05",
                "Cash_Weight": "0.3",
                "Asset_Class": "Bond",
                "Sub_Class": "US",
            },
        ]
        accounts = [
            {"Account": "Taxable", "Type": "Taxable", "Idle_Cash": "1000"},
        ]
        current_allocations = [
            {"Ticker": "VTI", "Account": "Taxable", "Shares": "42"},  # 5% over
            {"Ticker": "VXUS", "Account": "Taxable", "Shares": "29"},  # 3.33% under
            {"Ticker": "BND", "Account": "Taxable", "Shares": "28"},  # 6.67% under
        ]

        test_prices = {
            "VTI": Decimal("100"),
            "VXUS": Decimal("100"),
            "BND": Decimal("100"),
        }
        self.setup_price_mock(test_prices)

        # Total portfolio value = 1000 + 42*100 + 29*100 + 28*100 = 10900

        # Target allocation:
        # VTI: 10900 * 0.4 / 100 = 43 shares (4.76% increase, no rebalancing)
        # VXUS: 10900 * 0.3 / 100 = 32 shares (13.79% increase, needs rebalancing)
        # BND: 10900 * 0.3 / 100 = 32 shares (17.86% increase, needs rebalancing)

        manager = PortfolioManagerFactory.create_from_data(
            portfolio_weights, accounts, current_allocations
        )
        result = manager.rebalance()

        # Expected: VXUS and BND should be rebalanced
        expected_allocations = [
            {"Ticker": "VXUS", "Account": "Taxable", "Shares": 3, "Action": "buy"},
            {"Ticker": "BND", "Account": "Taxable", "Shares": 4, "Action": "buy"},
        ]

        self.assertEqual(result, expected_allocations)

    def test_new_investment_minimize_costs(self):
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
                "Vol": "0.05",
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
        ]
        current_allocations = [
            {"Ticker": "VTI", "Account": "Taxable", "Shares": "40"},
            {"Ticker": "VXUS", "Account": "Taxable", "Shares": "30"},
            {"Ticker": "BND", "Account": "Taxable", "Shares": "20"},
        ]

        test_prices = {
            "VTI": Decimal("100"),
            "VXUS": Decimal("100"),
            "BND": Decimal("100"),
            "GLD": Decimal("100"),
        }
        self.setup_price_mock(test_prices)

        # Total portfolio value = 10000 + 40*100 + 30*100 + 20*100 = 19000
        # Target allocation:
        # VTI: 19000 * 0.4 / 100 = 76 shares (90% increase, needs rebalancing)
        # VXUS: 19000 * 0.3 / 100 = 57 shares (90% increase, needs rebalancing)
        # BND: 19000 * 0.2 / 100 = 38 shares (90% increase, needs rebalancing)
        # GLD: 19000 * 0.1 / 100 = 19 shares (new investment, needs buying)

        manager = PortfolioManagerFactory.create_from_data(
            portfolio_weights, accounts, current_allocations
        )
        result = manager.rebalance()

        # Expected: All positions should be rebalanced, including buying the new GLD position
        expected_allocations = [
            {"Ticker": "GLD", "Account": "Taxable", "Shares": 19, "Action": "buy"},
            {"Ticker": "VXUS", "Account": "Taxable", "Shares": 27, "Action": "buy"},
            {"Ticker": "VTI", "Account": "Taxable", "Shares": 36, "Action": "buy"},
            {"Ticker": "BND", "Account": "Taxable", "Shares": 18, "Action": "buy"},
        ]

        self.assertEqual(result, expected_allocations)

    def test_allocation_with_insufficient_funds(self):
        portfolio_weights = [
            {
                "Ticker": "VTI",
                "Vol": "0.1",
                "Cash_Weight": "0.68",
                "Asset_Class": "Equity",
                "Sub_Class": "US",
            },
            {
                "Ticker": "VXUS",
                "Vol": "0.12",
                "Cash_Weight": "0.32",
                "Asset_Class": "Equity",
                "Sub_Class": "International",
            },
        ]
        accounts = [
            {"Account": "Taxable", "Type": "Taxable", "Idle_Cash": "100"},
        ]
        current_allocations = [
            {
                "Ticker": "VTI",
                "Account": "Taxable",
                "Shares": "600",
            },  # Slightly over-allocated but within 5%
            {"Ticker": "VXUS", "Account": "Taxable", "Shares": "250"},
        ]

        test_prices = {
            "VTI": Decimal("10"),
            "VXUS": Decimal("10"),
        }
        self.setup_price_mock(test_prices)

        # Total portfolio value = 600*10 + 250*10 = 8600
        # Target allocation:
        # VTI: 8600 * 0.68 = 5848 (target value)
        #     Current value: 600 * 10 = 6000
        #     Difference: |6000 - 5848| / 6000 = 0.025
        # VXUS: 8600 * 0.32 = 2720 (target value)
        #     Current value: 250 * 10 = 2500
        #     Need to buy: (2752 - 2500) / 10 = 25 shares

        manager = PortfolioManagerFactory.create_from_data(
            portfolio_weights, accounts, current_allocations
        )
        result = manager.rebalance()

        expected_allocations = [
            # Only have cash to buy 10 shares
            {"Ticker": "VXUS", "Account": "Taxable", "Shares": 10, "Action": "buy"},
        ]

        self.assertEqual(result, expected_allocations)


if __name__ == "__main__":
    unittest.main()
