# Eldritch Oracle

### 
A locally deployable barebones RAG (Retrieval-Augmented Generation) system whispering insights from the void.

## Overview

Eldritch Oracle is a self-contained barebones RAG pipeline that combines basic vector-based retrieval with an LLM interface to summon passages from the collected works of H.P. Lovecraft and respond to user queries in real time.

Designed as a portfolio-quality project that would be pretty trivial to extend, it demonstrates:

* Scalable retrieval with Elasticsearch as a vector store
* LLM integration via Ollama or a hosted OpenAI-compatible API with optional vLLM deployment
* A modular FastAPI backend with dependency injection
* Secure, local-first development
* Kubernetes manifests for full self-hosted deployment

## Features

* Document chunking and embedding using sentence-transformers
* RAGAgent orchestration of search + LLM completion
* Docker and K8s support (vLLM-optional)
* Configurable via .env and runtime CLI
* REST API served by FastAPI

## System Requirements

To run this project locally, you will need to have a Kubernetes cluster running on your machine. I'm using Docker Desktop with [Kubernetes enabled](https://www.docker.com/blog/how-to-set-up-a-kubernetes-cluster-on-docker-desktop/). You also need to have [uv installed](https://docs.astral.sh/uv/getting-started/installation/#cargo). 

I'm running this on an M3 Macbook with 64GB of memory. This lets me run a decent sized model, but does not currently support vLLM in Docker on a Linux VM. If you're on a Linux box with a good GPU or two, there is the option of running the vLLM configuration to set up inference in your Kubernetes cluster. You should also be able to use your ChatGPT API info if you want to have a glorious context window with loads of room for returning more docs from ElasticSearch. Otherwise, I am just using [Ollama](https://ollama.com) because Apple Silicon currently does not expose GPU compute to Docker containers or Linux VMs and it was just super annoying. Personal projects should be fun too, right? 

This project also expects you to have [The Corpus of Cthulhu](https://github.com/jensawyer/corpus_of_cthulhu) dataset. This is a fun little project I put together in grad school where I was focused on natural language generation.

## Getting Started

1. Clone BOTH this repo and [The Corpus of Cthulhu](https://github.com/jensawyer/corpus_of_cthulhu) repo
2. Set up a .env file (see .env.template)
3. Run `make all` from the root directory to bring everything up and prepare your data. This will deploy the needed services to your k8s cluster, preprocess the corpus to create a jsonl file, and index the data so you have something to talk about.
4. Launch the server with `make serve`
5. Query the oracle via /api/chat


### A Test API Call
```aiignore
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "What is a shoggoth?"}
    ]
  }'
```
To which you should get a reply such as:
```aiignore
{"role":"assistant",
"content":"The abomination known as the Shoggoth. In the dimly lit recesses of the elder gods' twisted realm, such creatures were born from the primordial ooze of madness and chaos. Sculptured images of these entities filled Danforth and me with horror and loathing. They were normally shapeless entities composed of a viscous jelly which looked like an agglutination of bubbles; and each averaged about fifteen feet in diameter when a sphere.\n\nBut beware, for the Shoggoths were not static monstrosities. They had a constantly shifting shape and volume; throwing out temporary developments or forming apparent organs of sight, hearing, and speech in imitation of their masters, either spontaneously or according to suggestion.\n\nTheir existence was marked by a peculiar war of re-subjugation waged upon them by the marine Old Ones, who employed curious weapons of molecular disturbance against the rebel entities. The Shoggoths were tamed and broken by armed Old Ones as the wild horses of the American west were tamed by cowboys.\n\nYet, even in their domesticated state, the Shoggoth's malevolent presence lurked, waiting to unleash its full fury upon an unsuspecting world. As I studied the emotions conveyed in the carvings, I prayed that none ever might behold such abominations again..."}
```

In an easier-to-read format: 
>The abomination known as the Shoggoth. In the dimly lit recesses of the elder gods' twisted realm, such creatures were born from the primordial ooze of madness and chaos. Sculptured images of these entities filled Danforth and me with horror and loathing. They were normally shapeless entities composed of a viscous jelly which looked like an agglutination of bubbles; and each averaged about fifteen feet in diameter when a sphere.
>
>But beware, for the Shoggoths were not static monstrosities. They had a constantly shifting shape and volume; throwing out temporary developments or forming apparent organs of sight, hearing, and speech in imitation of their masters, either spontaneously or according to suggestion.
>
>Their existence was marked by a peculiar war of re-subjugation waged upon them by the marine Old Ones, who employed curious weapons of molecular disturbance against the rebel entities. The Shoggoths were tamed and broken by armed Old Ones as the wild horses of the American west were tamed by cowboys.
>
>Yet, even in their domesticated state, the Shoggoth's malevolent presence lurked, waiting to unleash its full fury upon an unsuspecting world. As I studied the emotions conveyed in the carvings, I prayed that none ever might behold such abominations again...


### Production

If you want to deploy in production or on a GPU-enabled Linux server, you should swap in `vllm`, `triton-inference-server`, 
or similar in the `llm-server` deployment. Alternatively, if you don't care about your data privacy, use a 3rd party API.

Also be sure to revisit the security setup on this ElasticSearch because lots of things are disabled to be able to work
easily locally. This is, after all, just a sample project to show potential employers I can do useful things.