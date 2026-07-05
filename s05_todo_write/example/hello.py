"""Example module with greeting and arithmetic utilities."""


def greet(name: str) -> str:
    """Return a greeting message for the given name.

    Args:
        name: The person's name to greet.

    Returns:
        A formatted greeting string.
    """
    return f"Hello, {name}!"


def add(a: int, b: int) -> int:
    """Return the sum of two integers.

    Args:
        a: The first addend.
        b: The second addend.

    Returns:
        The sum of a and b.
    """
    return a + b


def main() -> None:
    """Run the main program logic."""
    print(greet("World"))
    print(add(2, 3))


if __name__ == "__main__":
    main()