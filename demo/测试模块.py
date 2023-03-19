
import unittest
from my_module import my_function

class TestMyFunction(unittest.TestCase):
    def test_my_function(self):
        self.assertEqual(my_function(3), 4)
        self.assertEqual(my_function(4), 5)
        self.assertEqual(my_function(5), 6)

if __name__ == '__main__':
    unittest.main()