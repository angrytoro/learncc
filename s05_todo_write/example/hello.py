"""Simple greeting and arithmetic example module.

This module provides basic functions for greeting people and
performing simple addition, intended as a demonstration of
type hints, docstrings, and a main guard.
"""


def greet(name: str, greeting: str = "Hello") -> str:
    """Return a personalised greeting string.

    Args:
        name: The name of the person to greet.
        greeting: The greeting word to use (default is "Hello").

    Returns:
        A formatted greeting string.
    """
    return f"{greeting}, {name}!"


def add(a: float, b: float) -> float:
    """Return the sum of two numbers.

    Args:
        a: The first addend.
        b: The second addend.

    Returns:
        The arithmetic sum of a and b.
    """
    return a + b


def main() -> None:
    """Run demonstration of module functions."""
    print(greet("World"))
    print(greet("Alice", "Hi"))
    print(add(3, 5))
    print(add(2.5, 3.7))


if __name__ == "__main__":
    main()
