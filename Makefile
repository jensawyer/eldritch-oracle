include .env
export

MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
K8S_DIR := $(MAKEFILE_DIR)k8s
ifeq ($(SELF_HOST_LLM),true)
  K8S_COMPONENTS := $(shell find $(K8S_DIR) -name '*.yaml')
else
  K8S_COMPONENTS := $(shell find $(K8S_DIR) -not -path "$(K8S_DIR)/vllm/*" -name '*.yaml')
endif

SELF_HOST_LLM ?= true

.PHONY: all check-env dev-up dev-down process-raw-corpus index download-vllm-model prepare-k8s check-es check-llm \
wait-for-ready prepare-document-data serve

all: dev-up prepare-document-data

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
	@echo "Waiting for pod with label '$(LABEL)' to become Ready..."
	@timeout 90 bash -c 'until kubectl get pods -l $(LABEL) -o jsonpath="{.items[0].status.conditions[?(@.type==\"Ready\")].status}" 2>/dev/null | grep -q True; do sleep 2; done' || \
	(echo "ERROR: Pod with label '$(LABEL)' did not become Ready in time." && exit 1)
	@echo "Pod with label '$(LABEL)' is Ready."

wait-for-es:
	@$(MAKE) wait-for-ready LABEL=app=elasticsearch

wait-for-llm:
	@$(MAKE) wait-for-ready LABEL=app=llm-server

check-es:
	@echo "Checking Elasticsearch connection and index at $(ES_HOST)..."
	cd scripts && uv run python3 test_es_connection.py

#check-llm:
#	@echo "Checking LLM inference backend availability at $(INFERENCE_API_URL)..."
#	cd scripts && uv run python3 test_llm_connection.py

check-llm:
	@echo "Testing raw curl to $(INFERENCE_API_URL)/v1/models..."
	@curl --fail --silent "$(INFERENCE_API_URL)/v1/models" || \
		(echo "ERROR: Could not connect to Ollama inference server or maybe you need to install the model $(INFERENCE_MODEL_NAME)" && exit 1)


download-vllm-model:
	cd scripts && uv run python3 download_model.py

process-raw-corpus:
	@echo "Preparing document chunks from raw corpus so we have something to index..."
	cd scripts && uv run python3 -m spacy download $(SPACY_MODEL) && uv run python3 prep_docs.py

index:
	@echo "Indexing document chunks into ElasticSearch..."
	cd scripts && uv run python3 index_chunks.py

prepare-document-data:
	@if [ ! -f "$(CORPUS_JSONL_FILE)" ]; then \
		echo "No preprocessed corpus found at $(CORPUS_JSONL_FILE). Running preprocessing..."; \
		$(MAKE) process-raw-corpus; \
	else \
		echo "Found preprocessed corpus at $(CORPUS_JSONL_FILE)"; \
	fi

	@$(MAKE) wait-for-es

	@echo "Checking Elasticsearch index..."
	@bash -c 'cd scripts && uv run python3 test_es_index.py'; \
	code=$$?; \
	if [ $$code -eq 2 ] || [ $$code -eq 3 ]; then \
		echo "Index is missing or empty, running indexing..."; \
		$(MAKE) index; \
	elif [ $$code -ne 0 ]; then \
		echo "Unexpected error while checking Elasticsearch (code $$code)"; \
		exit $$code; \
	fi


dev-up:
	@$(MAKE) check-env
	@if [ "$(SELF_HOST_LLM)" = "true" ]; then $(MAKE) prepare-vllm-k8s; fi
	@for comp in $(K8S_COMPONENTS); do \
	  echo "Applying $$comp..."; \
	  kubectl apply -f $$comp; \
	done
	@$(MAKE) wait-for-es
	@$(MAKE) check-es
	@if [ "$(SELF_HOST_LLM)" = "true" ]; then \
	  $(MAKE) wait-for-llm; \
	else \
	  echo "Waiting for external inference server at $(INFERENCE_API_URL)..."; \
	  timeout 30 bash -c 'until curl --silent --fail "$(INFERENCE_API_URL)/v1/models" > /dev/null; do sleep 2; done' || \
	    (echo "ERROR: Inference server did not respond in time" && exit 1); \
	fi
	@$(MAKE) check-llm


serve:
	@echo "Starting FastAPI server with Uvicorn..."
	uv run -- uvicorn main:app --port 8000 --workers 1

dev-down:
	@for comp in $(K8S_COMPONENTS); do \
	  echo "Deleting $$comp..."; \
	  kubectl delete -f $$comp --ignore-not-found; \
	done
