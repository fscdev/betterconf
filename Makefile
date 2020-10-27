py := poetry run

install:
	pip install poetry
	poetry install

test:
	$(py) pytest

black:
	$(py) black betterconf/

pre-commit:
	$(py) pre-commit install

mypy:
	$(py) mypy betterconf/
