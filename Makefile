include .env
export

MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
K8S_DIR := $(MAKEFILE_DIR)k8s
ifeq ($(SELF_HOST_LLM),true)
  K8S_COMPONENTS := $(shell find $(K8S_DIR) -name '*.yaml')
else
  K8S_COMPONENTS := $(shell find $(K8S_DIR) -not -path "$(K8S_DIR)/llm/*" -name '*.yaml')
endif

SELF_HOST_LLM ?= true

.PHONY: all check-env dev-up dev-down process-raw-corpus index download-vllm-model prepare-k8s check-es check-llm wait-for-ready

all: download-vllm-model process-raw-corpus dev-up index

check-env:
	@echo "Validating environment configuration..."
	@echo "SELF_HOST_LLM: $(SELF_HOST_LLM)"
	@if [ "$(SELF_HOST_LLM)" = "true" ]; then \
		if [ -z "$(LLM_MODEL_PATH)" ]; then \
			echo "ERROR: LLM_MODEL_PATH is not set in .env"; \
			exit 1; \
		fi; \
		if [ ! -f "$(LLM_MODEL_PATH)" ]; then \
			echo "ERROR: Model file not found at $(LLM_MODEL_PATH)"; \
			exit 1; \
		fi; \
		echo "Model file exists at $(LLM_MODEL_PATH)"; \
		unameOut=$$(uname); \
		if [ "$$unameOut" = "Darwin" ]; then \
			echo "WARNING: vLLM is not GPU-compatible with macOS. You should set SELF_HOST_LLM=false."; \
		fi; \
	else \
		if [ -z "$(INFERENCE_API_URL)" ]; then \
			echo "ERROR: INFERENCE_API_URL is not set in .env or as global environment variable."; \
			exit 1; \
		fi; \
		if [ -z "$(INFERENCE_API_KEY)" ]; then \
			echo "ERROR: INFERENCE_API_KEY is not set in .env or as global environment variable."; \
			exit 1; \
		fi; \
		if [ -z "$(INFERENCE_MODEL_NAME)" ]; then \
			echo "ERROR: INFERENCE_MODEL_NAME is not set in .env or as global environment variable."; \
			exit 1; \
		fi; \
		echo "Inference API config looks good:"; \
		echo "   → URL: $(INFERENCE_API_URL)"; \
		echo "   → Model: $(INFERENCE_MODEL_NAME)"; \
	fi

prepare-vllm-k8s:
	@echo "Preparing K8s manifests..."
ifeq ($(SELF_HOST_LLM),true)
	@envsubst < k8s/llm/llm-deployment.yaml.template > k8s/llm/llm-deployment.yaml
	@envsubst < k8s/llm/llm-pv.yaml.template > k8s/llm/llm-pv.yaml
endif

wait-for-ready:
	@if [ -z "$(LABEL)" ]; then \
		echo "ERROR: You must pass LABEL (e.g. make wait-for-ready LABEL=app=elasticsearch)"; \
		exit 1; \
	fi
	@echo "⏳ Waiting for pod with label '$(LABEL)' to become Ready..."
	@timeout 90 bash -c 'until kubectl get pods -l $(LABEL) -o jsonpath="{.items[0].status.conditions[?(@.type==\"Ready\")].status}" 2>/dev/null | grep -q True; do sleep 2; done' || \
	(echo "ERROR: Pod with label '$(LABEL)' did not become Ready in time." && exit 1)
	@echo "Pod with label '$(LABEL)' is Ready."

wait-for-es:
	@$(MAKE) wait-for-ready LABEL=app=elasticsearch

wait-for-llm:
	@$(MAKE) wait-for-ready LABEL=app=llm-server

check-es:
	@echo "🔍 Checking Elasticsearch connection and index at $(ES_HOST)..."
	cd scripts && python3 test_es_connection.py

check-llm:
	@echo "🔍 Checking LLM inference backend availability..."
	cd scripts && python3 test_llm_connection.py

download-vllm-model:
	cd scripts && python3 download_model.py

process-raw-corpus:
	@echo "Preparing document chunks from raw corpus so we have something to index..."
	cd scripts && python3 -m spacy download $(SPACY_MODEL) && python3 prep_docs.py

index:
	@echo "Indexing document chunks into ElasticSearch..."
	cd scripts && python3 index_chunks.py

dev-up:
	@$(MAKE) check-env

	@if [ "$(SELF_HOST_LLM)" = "true" ]; then \
	  @$(MAKE) prepare-vllm-k8s \
	fi

	@for comp in $(K8S_COMPONENTS); do \
	  echo "Applying $$comp..."; \
	  kubectl apply -f $$comp; \
	done

	@$(MAKE) wait-for-es
	@$(MAKE) check-es

	@if [ "$(SELF_HOST_LLM)" = "true" ]; then \
	  $(MAKE) wait-for-llm; \
	fi

	@$(MAKE) check-llm



dev-down:
	@for comp in $(K8S_COMPONENTS); do \
	  echo "Deleting $$comp..."; \
	  kubectl delete -f $$comp --ignore-not-found; \
	done
