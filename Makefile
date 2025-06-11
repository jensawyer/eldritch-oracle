include .env
export

MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
K8S_DIR := $(MAKEFILE_DIR)k8s
K8S_COMPONENTS := $(shell find $(K8S_DIR) -name '*.yaml')

SELF_HOST_LLM ?= true

.PHONY: all check-env dev-up dev-down process index download-model prepare-k8s

all: download-model process dev-up index

check-env:
	@echo "Validating environment configuration..."
	@echo "SELF_HOST_LLM: $(SELF_HOST_LLM)"

ifeq ($(SELF_HOST_LLM),true)
	@if [ -z "$(LLM_MODEL_PATH)" ]; then \
		echo "ERROR: LLM_MODEL_PATH is not set in .env"; \
		exit 1; \
	fi

	@if [ ! -f "$(LLM_MODEL_PATH)" ]; then \
		echo "ERROR: Model file not found at $(LLM_MODEL_PATH)"; \
		exit 1; \
	fi

	@echo "Model file exists at $(LLM_MODEL_PATH)"

	@unameOut=$$(uname); \
	if [ "$$unameOut" = "Darwin" ]; then \
		echo "WARNING: vLLM is not GPU-compatible with macOS. You should set SELF_HOST_LLM=false."; \
	fi
else
	@if [ -z "$(INFERENCE_API_URL)" ]; then \
		echo "ERROR: INFERENCE_API_URL is not set in .env or as global environment variable."; \
		exit 1; \
	fi

	@if [ -z "$(INFERENCE_API_KEY)" ]; then \
		echo "ERROR: INFERENCE_API_KEY is not set in .env or as global environment variable."; \
		exit 1; \
	fi

	@if [ -z "$(INFERENCE_MODEL_NAME)" ]; then \
		echo "ERROR: INFERENCE_MODEL_NAME is not set in .env or as global environment variable."; \
		exit 1; \
	fi

	@echo "Inference API config looks good:"
	@echo "   → URL: $(INFERENCE_API_URL)"
	@echo "   → Model: $(INFERENCE_MODEL_NAME)"
endif


download-model:
	cd scripts && python3 download_model.py

process:
	cd scripts && python3 prep_docs.py

index:
	cd scripts && python3 index_chunks.py

prepare-k8s:
	@echo "Preparing K8s manifests..."
	@envsubst < k8s/llm/llm-deployment.yaml.template > k8s/llm/llm-deployment.yaml
	@envsubst < k8s/llm/llm-pv.yaml.template > k8s/llm/llm-pv.yaml

dev-up: check-env prepare-k8s
	@for comp in $(K8S_COMPONENTS); do \
	  echo "Applying $$comp..."; \
	  kubectl apply -f $(K8S_DIR)/$$comp; \
	done

ifeq ($(SELF_HOST_LLM),true)
	@echo "Waiting for LLM server pod to appear..."
	@timeout 60 bash -c 'until kubectl get pods -l app=llm-server | grep Running; do sleep 2; done' || \
	  (echo "ERROR: LLM pod never appeared" && exit 1)

	@echo "Verifying LLM server is responding..."
	@sleep 2
	@curl --fail --silent http://localhost:30800/v1/models > /dev/null && \
	  echo "LLM server is up at http://localhost:30800" || \
	  (echo "ERROR: LLM server did not respond as expected" && exit 1)
else
	@echo "Using Ollama or external inference backend"
	@curl --fail --silent $(INFERENCE_API_URL)/v1/models > /dev/null && \
	  echo "Able to reach LLM inference server at $(INFERENCE_API_URL)" || \
	  (echo "ERROR: Could not reach LLM inference server at $(INFERENCE_API_URL). Is it running?" && exit 1)
endif

dev-down:
	@for comp in $(K8S_COMPONENTS); do \
	  echo "Deleting $$comp..."; \
	  kubectl delete -f $$comp --ignore-not-found; \
	done
