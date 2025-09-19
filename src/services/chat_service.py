import logging

from models.chat import ChatMessage, ChatRequest
from services.search_service import ESSearch
from core.config import Config


class RAGAgent:
    def __init__(self, config: Config, search_service: ESSearch):
        self.openai_client = config.openai_client
        self.search_service = search_service
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    def generate_response(self, request: ChatRequest) -> ChatMessage:
        """
        This is a super basic RAG flow so we are doing no fancy things or introducing any elaborate libraries. This is to
        demonstrate what barebones RAG actually looks like. With a big context window, you can actually do a lot before
        getting into adding extra complexity.

        The flow is as follows:
        1. Use the user message to query for the docs in ElasticSearch that are most similar
        2. Use the search results as part of the system prompt which is sent along with the user's message to the LLM
        which will then factor the whole thing into the generated response.

        :param request:
        :return: The response message from the assistant.
        """
        # First we use the user query to get the relevant chunk(s) from our ES service. These are joined and used to contribute to
        # the system prompt
        context_chunks: list[str] = self.search_service.search(
            request.messages, top_k=1
        )
        context_text = "\n\n".join(c for c in context_chunks)
        # This must be kept really small for our purposes on a local machine as Ollama defaults to a very small context window
        # and we're using the default via the OpenAI client. It's easy to enlarge to what the model can handle via the real
        # Ollama interface.
        sys_prompt = f"""You are an assistant that is an expert on H.P. Lovecraft's work.
You will answer questions with excerpts from H.P. Lovecraft's stories which you may explain or summarize in the style of Lovecraft.
Do not offer additional followup questions because you will have no memory of what you said before.
Always bring the topic back to Lovecraft's stories. You do not write or talk about code. You refuse to engage in thought experiments.
You must use the following context to help write your reply: {context_text}"""
        final_prompt = []
        final_prompt.append({"role": "system", "content": sys_prompt})
        # Add the incoming conversation messages
        final_prompt.extend([msg.model_dump() for msg in request.messages])
        self.logger.debug(final_prompt)
        response = self.openai_client.chat.completions.create(
            model=self.config.inference_model_name,
            messages=final_prompt,
            max_tokens=1024,
            temperature=0.5,
        )
        return ChatMessage(
            role="assistant", content=response.choices[0].message.content
        )
