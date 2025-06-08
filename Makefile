
.PHONY: all dev-up dev-down process index

all: process dev-up index

process:
	cd scripts && python3 prep_docs.py

index:
	cd scripts && python3 index_chunks.py

dev-up:
	kubectl apply -f k8s
	@kubectl wait --for=condition=ready pod -l app=elasticsearch --timeout=120s
	@echo "Elasticsearch ready at localhost:30920"

dev-down:
	kubectl delete -f k8s
