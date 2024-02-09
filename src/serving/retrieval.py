import os
from operator import itemgetter
from textwrap import dedent

from dotenv import load_dotenv
from langchain_community.vectorstores.pinecone import Pinecone
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.pydantic_v1 import BaseModel
from langchain_core.runnables import RunnableParallel

load_dotenv()
OPENAI_KEY = os.environ.get('OPENAI_KEY')
YOUTUBE_USER_HANDLE = os.environ.get('YOUTUBE_USER_HANDLE')


def make_multiquery(model, retriever, input):
  MULTI_QUERY_PT_RAW = dedent("""
  You are a search engine expert.

  TASK: Generate 2 different versions of the given USER QUESTION and (optionally) CHAT HISTORY
  in order to retrive the most relevant documents from a (vector) database based on semantic similarity.

  RULES:
      - Generate the question from multiple different perspectives, focusing on unique angles
      about the important aspects of the question.
      - Provide these alternative  questions separated by newlines.

  QUESTION:
  {question}

  CHAT HISTORY (blank if none):
  {chat_history}
  """)

  pt_formatted = MULTI_QUERY_PT_RAW.format(
      question="{question}",
      chat_history=input.get('chat_history', 'N/A')
  )
  return MultiQueryRetriever.from_llm(
    retriever=retriever,
    llm=model,
    prompt=PromptTemplate.from_template(pt_formatted)
  )

def get_retrieval_chain(youtube_user_handle, openai_api_key):
    db = Pinecone.from_existing_index(
        'youtube-videos',
        namespace=youtube_user_handle,
        embedding=OpenAIEmbeddings(
            model='text-embedding-3-small',
            openai_api_key=openai_api_key
        )
    )


    retriever = db.as_retriever(search_type='similarity', search_kwargs={'k': 4})

    model = ChatOpenAI(temperature=0, openai_api_key=OPENAI_KEY)

    # RAG prompt
    SYSTEM_PROMPT = dedent(
        """
        Answer the question concisely based only on the following transcript snippets from a youtube video.
        Do not mention the snippets directly. If you don't know the answer, simply say 'I don't know'.
        A chat history may be provided for additional context.

        CHAT HISTORY:
        {chat_history}


        SNIPPETS:
        {context}
        """
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", "Question:\n{question}")
        ]
    )

    # RAG
    chain = (
        {
            "context": itemgetter("question") | retriever,
            "question": lambda input: input['question'],
            "chat_history": lambda input: input.get('chat_history', 'N/A')
        }
        | prompt
        | model
        | StrOutputParser()
    )

    # Add typing for input
    class Question(BaseModel):
        question: str
        chat_history: str = ""


    chain = chain.with_types(input_type=Question)


    return chain


# Expose chain
chain = get_retrieval_chain(youtube_user_handle=YOUTUBE_USER_HANDLE, openai_api_key=OPENAI_KEY)
