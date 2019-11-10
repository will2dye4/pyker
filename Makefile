clean:
	pip3 uninstall -y pyker

install:
	pip3 install --ignore-installed . || pip3 install --ignore-installed --user .
