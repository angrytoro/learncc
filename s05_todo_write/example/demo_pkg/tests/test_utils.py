"""Tests for the demo_pkg utility functions.

Uses Python's built-in unittest framework.
"""

import unittest
from demo_pkg.utils import (
    factorial,
    is_prime,
    reverse_string,
    celsius_to_fahrenheit,
    fibonacci,
)


class TestFactorial(unittest.TestCase):
    """Test cases for the factorial function."""

    def test_factorial_zero(self) -> None:
        self.assertEqual(factorial(0), 1)

    def test_factorial_one(self) -> None:
        self.assertEqual(factorial(1), 1)

    def test_factorial_small(self) -> None:
        self.assertEqual(factorial(5), 120)

    def test_factorial_large(self) -> None:
        self.assertEqual(factorial(10), 3_628_800)

    def test_factorial_negative(self) -> None:
        with self.assertRaises(ValueError):
            factorial(-1)


class TestIsPrime(unittest.TestCase):
    """Test cases for the is_prime function."""

    def test_prime_2(self) -> None:
        self.assertTrue(is_prime(2))

    def test_prime_3(self) -> None:
        self.assertTrue(is_prime(3))

    def test_non_prime_4(self) -> None:
        self.assertFalse(is_prime(4))

    def test_prime_17(self) -> None:
        self.assertTrue(is_prime(17))

    def test_non_prime_20(self) -> None:
        self.assertFalse(is_prime(20))

    def test_edge_invalid(self) -> None:
        with self.assertRaises(ValueError):
            is_prime(1)
        with self.assertRaises(ValueError):
            is_prime(0)
        with self.assertRaises(ValueError):
            is_prime(-5)


class TestReverseString(unittest.TestCase):
    """Test cases for the reverse_string function."""

    def test_reverse_basic(self) -> None:
        self.assertEqual(reverse_string("hello"), "olleh")

    def test_reverse_empty(self) -> None:
        self.assertEqual(reverse_string(""), "")

    def test_reverse_palindrome(self) -> None:
        self.assertEqual(reverse_string("racecar"), "racecar")

    def test_reverse_with_spaces(self) -> None:
        self.assertEqual(reverse_string("a b c"), "c b a")


class TestCelsiusToFahrenheit(unittest.TestCase):
    """Test cases for the celsius_to_fahrenheit function."""

    def test_freezing(self) -> None:
        self.assertEqual(celsius_to_fahrenheit(0.0), 32.0)

    def test_boiling(self) -> None:
        self.assertEqual(celsius_to_fahrenheit(100.0), 212.0)

    def test_negative(self) -> None:
        self.assertEqual(celsius_to_fahrenheit(-40.0), -40.0)

    def test_room_temp(self) -> None:
        self.assertAlmostEqual(celsius_to_fahrenheit(22.0), 71.6)


class TestFibonacci(unittest.TestCase):
    """Test cases for the fibonacci function."""

    def test_fib_zero(self) -> None:
        self.assertEqual(fibonacci(0), 0)

    def test_fib_one(self) -> None:
        self.assertEqual(fibonacci(1), 1)

    def test_fib_two(self) -> None:
        self.assertEqual(fibonacci(2), 1)

    def test_fib_ten(self) -> None:
        self.assertEqual(fibonacci(10), 55)

    def test_fib_negative(self) -> None:
        with self.assertRaises(ValueError):
            fibonacci(-1)


if __name__ == "__main__":
    unittest.main()
