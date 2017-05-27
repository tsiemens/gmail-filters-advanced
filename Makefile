
.PHONY: initenv checkenv update test

checkenv:
ifeq ($(VIRTUAL_ENV),)
	$(error You must source env/bin/activate)
endif

initenv:
	virtualenv -p python3 env

update: checkenv
	pip3 install -r requirements.txt

test: checkenv
	test/GmailFilterParserTest.py
	test/GmailFilterTemplateTest.py
