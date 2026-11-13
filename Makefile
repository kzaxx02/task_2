.PHONY: run test

run:
	./run.sh $(ARGS)

test:
	PYTHONPATH=src python3 -m unittest discover -s tests -v
