
.PHONY: all dev-up dev-down process index

all: process dev-up index

process:
	cd scripts && python3 prep_docs.py

index:
	cd scripts && python3 index_chunks.py

dev-up:
	@for comp in $(K8S_COMPONENTS); do \
	  echo "🚀 Applying $$comp..."; \
	  kubectl apply -f $(K8S_DIR)/$$comp; \
	done
	@echo "⏳ Waiting for Elasticsearch to become ready..."
	@kubectl wait --for=condition=ready pod -l app=elasticsearch --timeout=120s
	@echo "✅ Elasticsearch is up at localhost:30920"

dev-down:
	@for comp in $(K8S_COMPONENTS); do \
	  echo "🧹 Deleting $$comp..."; \
	  kubectl delete -f $(K8S_DIR)/$$comp --ignore-not-found; \
	done
