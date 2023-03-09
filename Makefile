env : .venv/bin/activate

.venv/bin/activate : requirements.txt
	test -d .venv || python3 -m venv .venv
	. .venv/bin/activate; pip install --upgrade pip setuptools wheel; pip install -Ur requirements.txt ; pip install --editable .
	touch .venv/bin/activate

clean:
	rm -rf .venv
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete

test:
	.venv/bin/python -m pytest test
