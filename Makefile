.PHONY: test

test:
	python3 -m unittest discover -s tests -v
	node --test extension/spatial.test.mjs
	bash -n install/install.sh
	bash tests/test_install_dry_run.sh
