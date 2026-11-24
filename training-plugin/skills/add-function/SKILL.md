---
name: add-function
description: Add a new function to a Python file in src/ following the project checklist. Use when the user asks to add or create a function.
disable-model-invocation: true
argument-hint: <file> <function description>
---

Add a new function to the Python file in src/, following this checklist in order.

Request: $ARGUMENTS

1. Read the target file first, so the new function matches its style.
2. Write the function with type hints on every parameter and the return value.
3. Add a docstring that starts with `[py-rule]`.
4. Handle the obvious edge cases (for example division by zero, empty input) by raising a clear error.
5. Finish with the line `Added with the training-plugin add-function skill` so it is obvious the plugin skill ran.
