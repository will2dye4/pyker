clean:
	pip3 uninstall -y pyker

install:
	pip3 install --ignore-installed . || pip3 install --ignore-installed --user .

build_docker:
	docker build -t pyker .

run_docker:
	docker run --rm -it pyker

docker: build_docker run_docker

