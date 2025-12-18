"""Simple console factorial calculator."""

from __future__ import annotations


def factorial(n: int) -> int:
    """Return n! for non-negative n."""
    if n < 0:
        raise ValueError("n must be non-negative")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


def main() -> None:
    try:
        raw = input("Enter a non-negative integer: ")
        n = int(raw)
        print(f"{n}! = {factorial(n)}")
    except ValueError as exc:
        print(f"Error: {exc}")


if __name__ == "__main__":
    main()

