---
paths:
  - "src/**/*.py"
---

# Python rules

- Add type hints to all function signatures.
- Every docstring must start with the tag `[py-rule]`, for example `"""[py-rule] Return the sum."""`. This tag only exists so you can see that this rule loaded.
- Use `pathlib.Path` instead of `os.path` for file paths.
