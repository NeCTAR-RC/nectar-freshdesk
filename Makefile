PROJECT=freshdesk
REPO=registry.rc.nectar.org.au/nectar

SHA=$(shell git rev-parse --verify --short HEAD)
TAG=$(REPO)/$(PROJECT):$(SHA)


build:
	docker build -t $(TAG) .

push:
	docker push $(TAG)

.PHONY: build push
