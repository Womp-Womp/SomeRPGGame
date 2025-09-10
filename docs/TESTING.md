# Testing AstraRPG

We use `pytest` for unit tests. CI runs tests on Windows and Linux for Python 3.11/3.12.

## Setup

```bash
pip install -r requirements-dev.txt
```

If you need runtime deps:

```bash
pip install -r requirements.txt
```

## Run

```bash
pytest -q
```

With coverage:

```bash
pytest --cov=astrarpg --cov-report=term-missing
```

## Layout

```
tests/
  test_generation.py   # seed + RNG determinism
  test_combat.py       # combat math sanity
  test_commands.py     # dispatcher basics
```
