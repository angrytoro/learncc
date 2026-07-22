"""Utility functions for the demo_pkg package."""


def factorial(n: int) -> int:
    """Return the factorial of a non-negative integer n.

    Args:
        n: A non-negative integer.

    Returns:
        The factorial of n (n!).

    Raises:
        ValueError: If n is negative.
    """
    if n < 0:
        raise ValueError("factorial requires a non-negative integer")
    if n == 0:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


def is_prime(n: int) -> bool:
    """Determine whether a positive integer n is prime.

    Args:
        n: A positive integer greater than 1.

    Returns:
        True if n is prime, False otherwise.

    Raises:
        ValueError: If n <= 1.
    """
    if n <= 1:
        raise ValueError("is_prime requires an integer > 1")
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


def reverse_string(text: str) -> str:
    """Return the reversed version of the input string.

    Args:
        text: The string to reverse.

    Returns:
        The reversed string.
    """
    return text[::-1]


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert a temperature from Celsius to Fahrenheit.

    Args:
        celsius: Temperature in degrees Celsius.

    Returns:
        Temperature in degrees Fahrenheit.
    """
    return (celsius * 9.0 / 5.0) + 32.0


def fibonacci(n: int) -> int:
    """Return the nth Fibonacci number (0-indexed).

    Args:
        n: A non-negative integer (0-indexed position).

    Returns:
        The nth Fibonacci number (F0 = 0, F1 = 1).

    Raises:
        ValueError: If n is negative.
    """
    if n < 0:
        raise ValueError("fibonacci requires a non-negative integer")
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
