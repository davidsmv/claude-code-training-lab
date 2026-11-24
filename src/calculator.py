def add(a: int | float, b: int | float) -> int | float:
    """[py-rule] Return the sum of a and b."""
    return a + b


def divide(a: int | float, b: int | float) -> int | float:
    """[py-rule] Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
