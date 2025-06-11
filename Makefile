include .env
export

MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
K8S_DIR := $(MAKEFILE_DIR)k8s
K8S_COMPONENTS := $(shell find $(K8S_DIR) -name '*.yaml')

.PHONY: all dev-up dev-down process index

all: download-model process dev-up index

USE_OLLAMA ?= false

	@echo "🔍 Validating environment configuration..."
	@echo "🔄 Inference backend: $(USE_OLLAMA)"

ifeq ($(USE_OLLAMA),false)
	@if [ -z "$(LLM_MODEL_PATH)" ]; then \
		echo "❌ LLM_MODEL_PATH is not set in .env"; \
		exit 1; \
	fi

	@if [ ! -f "$(LLM_MODEL_PATH)" ]; then \
		echo "❌ Model file not found at $(LLM_MODEL_PATH)"; \
		exit 1; \
	fi

	@echo "✅ Model file exists at $(LLM_MODEL_PATH)"

	@unameOut=$$(uname); \
	if [ "$$unameOut" = "Darwin" ]; then \
		echo "⚠️  vLLM is not GPU-compatible with macOS. You should probably set USE_OLLAMA=true."; \
	fi
else
	@echo "🟢 Ollama is enabled — skipping model file check"
endif

download-model:
	cd scripts && python3 download_model.py

process:
	cd scripts && python3 prep_docs.py

index:
	cd scripts && python3 index_chunks.py

prepare-k8s:
	@echo "🔧 Preparing K8s manifests..."
	@envsubst < k8s/llm/llm-deployment.yaml.template > k8s/llm/llm-deployment.yaml
	@envsubst < k8s/llm/llm-pv.yaml.template > k8s/llm/llm-pv.yaml


dev-up: prepare-k8s
	@for comp in $(K8S_COMPONENTS); do \
	  echo "🚀 Applying $$comp..."; \
	  kubectl apply -f $(K8S_DIR)/$$comp; \
	done

ifeq ($(USE_OLLAMA),false)
	@echo "⏳ Waiting for LLM server pod to appear..."
	@timeout 60 bash -c 'until kubectl get pods -l app=llm-server | grep Running; do sleep 2; done' || \
	  (echo "❌ LLM pod never appeared" && exit 1)
	@echo "🔍 Verifying LLM server is responding..."
	@sleep 2
	@curl --fail --silent http://localhost:30800/v1/models > /dev/null && \
	  echo "✅ LLM server is up at http://localhost:30800" || \
	  (echo "❌ LLM server did not respond as expected" && exit 1)
else
	@echo "ℹ️ Using Ollama for local inference. Be sure Ollama is running and the model is pulled."
	@curl --fail --silent http://localhost:11434/api/tags > /dev/null && \
	  echo "✅ Ollama appears to be running." || \
	  (echo "❌ Could not reach Ollama. Is it running?" && exit 1)
endif


dev-down:
	@for comp in $(K8S_COMPONENTS); do \
	  echo "🧹 Deleting $$comp..."; \
	  kubectl delete -f $$comp --ignore-not-found; \
	done
