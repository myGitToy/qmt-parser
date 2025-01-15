import unittest
import pandas as pd
from datetime import datetime
from apt.vendor.akshare.security import security

class TestSecurity(unittest.TestCase):

    def setUp(self):
        self.sec = security()
        self.code = '601318.sh'
        self.sec.start_date = datetime(2020, 1, 1)
        self.sec.end_date = datetime(2022, 1, 1)

    def test_get_trade_date(self):
        """
        需要测试返回的是dataframe，并且有code|date|is_open|pretrade_date这几列
        AssertionError:      code       date  is_open pretrade_date
        0    None 2021-12-31        1    2021-12-30
        1    None 2021-12-30        1    2021-12-29
        2    None 2021-12-29        1    2021-12-28
        """
        trade_dates = self.sec.get_trade_date()
        self.assertIsInstance(trade_dates, pd.DataFrame)
        self.assertGreater(len(trade_dates), 0)
        expected_columns = ['code', 'date', 'is_open', 'pretrade_date']
        self.assertTrue(all(column in trade_dates.columns for column in expected_columns))

if __name__ == '__main__':
    unittest.main()