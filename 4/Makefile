.PHONY: run test compare

run:
	./run.sh $(ARGS)

test:
	PYTHONPATH=src:scripts python3 -m unittest discover -s tests -v

compare:
	PYTHONPATH=src python3 scripts/compare_with_pip.py $(REPO) $(PKG)
