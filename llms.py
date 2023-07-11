import os
import openai
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI as LChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain import PromptTemplate
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document

# Initial config 
openai_api_key=os.getenv("OPENAI_API_KEY")
with open('map_prompt.txt', "r") as file:
    MAP_PROMPT = file.read()
with open('combine_prompt.txt', "r") as file:
    COMBINE_PROMPT = file.read()
with open('simple_prompt.txt', "r") as file:
    SIMPLE_PROMPT = file.read()
CHUNK_SIZE = 3600
OVERLAP = 100

class ChatOpenAI:
    def __init__(self, model_name, temperature, openai_api_key):
        self.model_name = model_name
        self.temperature = temperature
        self.openai_api_key = openai_api_key

    def generate_response(self, messages):
        response = openai.ChatCompletion.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature,
            n=1,
            stop=None
        )
        return response.choices[0].message['content'].strip()

# OpenAI based ChatOpenAI instance
ollm35 = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0, openai_api_key=openai_api_key)
# LangChain ChatOpenAI instance
llm35 = LChatOpenAI(model_name='gpt-3.5-turbo',temperature=0, openai_api_key=openai_api_key)


def get_num_tokens(text):
    # Use LangChain version
    return llm35.get_num_tokens(text)

def get_bullets(text, ntokens, map_prompt=MAP_PROMPT, combine_prompt = COMBINE_PROMPT, \
                simple_prompt=SIMPLE_PROMPT, chunk_size=CHUNK_SIZE, overlap=OVERLAP):

    if ntokens < 3900:      
        # Use direct summary when not hitting token limits
        messages = [
        {"role": "system", "content": simple_prompt},
        {"role": "user", "content": text[0]}
                ]
        summary = ollm35.generate_response(messages)
        return (summary, 0, 0)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
    docs = text_splitter.create_documents(text)

    map_prompt_template = PromptTemplate(template=map_prompt, input_variables=["text"])
    combine_prompt_template = PromptTemplate(template=combine_prompt, input_variables=["text"])

    summary_chain = load_summarize_chain(llm=llm35,
                                    chain_type='map_reduce',
                                    map_prompt=map_prompt_template,
                                    combine_prompt=combine_prompt_template,
#                                      verbose=True
                                    )
    
    summary = summary_chain.run(docs)
    return (summary, chunk_size, overlap)