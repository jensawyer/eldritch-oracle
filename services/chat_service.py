from models.chat import ChatMessage, ChatRequest
from services.search_service import ESSearch
from core.config import Config

class RAGAgent:

    def __init__(self, config:Config, search_service:ESSearch):
        self.openai_client = config.openai_client
        self.search_service = search_service
        self.config = config

    def generate_response(self, request:ChatRequest) -> ChatMessage:
        context_chunks = self.search_service.search(request.messages, top_k=2)
        context = []
        for hit in context_chunks['hits']['hits']:
            del hit['_source']['embedding']
            context.append(str(hit['_source']))
        context_text = "\n\n".join(c for c in context)
        print(context_text)
        sys_prompt = f"""You are an expert on H.P. Lovecraft's work that likes to speak in his writing style.
You will answer questions with excerpts from H.P. Lovecraft's stories which you may explain or summarize. Relevant context you must use for for your reply: 
{context_text}"""
        final_prompt = []
        final_prompt.append({"role": "system", "content": sys_prompt})
        final_prompt.append(*[msg.dict() for msg in request.messages])
        response = self.openai_client.chat.completions.create(model=self.config.inference_model_name,
                                                              messages=final_prompt,
                                                              max_tokens=1024,
                                                              temperature=0.4)
        print(response)
        return ChatMessage(role="assistant", content=response.choices[0].message.content)




# def generate_response(request: ChatRequest) -> ChatMessage:
#     """
#     Core RAG logic:
#     1. Retrieve relevant context from ES
#     2. Compose a system + user prompt
#     3. Call the LLM API and return response
#     """
#     # Step 1: Retrieve context (stub for now)
#     context_chunks = retrieve_relevant_chunks(request.messages)
#
#     # Step 2: Compose final prompt
#     context_text = "\n\n".join(chunk["content"] for chunk in context_chunks)
#     final_prompt = [
#         {"role": "system", "content": f"You are an expert on H.P. Lovecraft's work.\n\nRelevant context:\n{context_text}"},
#         *[msg.dict() for msg in request.messages]
#     ]
#
#     # Step 3: Call LLM (stub for now)
#     response_text = "This is a stubbed response."

    # return ChatMessage(role="assistant", content=response_text)
