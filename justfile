login:
	poetry run python main.py --login

ran:
	poetry run python main.py

update-secret:
	gh secret set GARMIN_TOKENS -b$(GARMIN_TOKENS)