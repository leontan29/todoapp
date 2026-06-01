.PHONY: commit push unit full

MSG ?=

commit:
	git add -A
	git commit -m "$(MSG)"

push:
	git push

unit:
	pytest tests/test_auth.py tests/test_session.py

full:
	pytest tests/
