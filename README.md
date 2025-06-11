###  Why I'm Using Ollama for Local Inference

This project uses [Ollama](https://ollama.com) to serve LLaMA models locally on macOS. We do this because Apple Silicon 
does not expose GPU compute to Docker containers or Linux VMs, and vLLM or similar libraries require GPU access.

### Other services expect you to have a local K8s cluster

### Local Development

For local development, just run:

### Production

If you want to deploy in production or on a GPU-enabled Linux server, you should swap in `vllm`, `triton-inference-server`, 
or similar in the `llm-server` deployment. Alternatively, if you don't care about your data privacy, use a 3rd party API.

Also be sure to revisit the security setup on this ElasticSearch because lots of things are disabled to be able to work
easily locally. This is, after all, just a sample project to show potential employers I can do useful things.