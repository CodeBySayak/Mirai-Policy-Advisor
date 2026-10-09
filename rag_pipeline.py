import os
from typing import List, Dict, Any, Tuple
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from config import settings

class RAGPipeline:
    def __init__(self):
        self.embeddings = None
        self.llm = None
        
        if settings.google_api_key:
            self.embeddings = GoogleGenerativeAIEmbeddings(model=settings.embedding_model, google_api_key=settings.google_api_key)
            self.llm = ChatGoogleGenerativeAI(model=settings.generation_model, temperature=0.0, google_api_key=settings.google_api_key)
        
        self.vector_store = None
        if os.path.exists(settings.chroma_db_dir) and self.embeddings:
            try:
                self.vector_store = Chroma(
                    persist_directory=settings.chroma_db_dir,
                    embedding_function=self.embeddings
                )
            except Exception as e:
                print(f"Failed to load existing vector store: {e}")

        # The system prompt enforces strict rules
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are the MirAI Student Policy Advisor, an AI assistant for Mirai School of Technology.
Your sole purpose is to answer student questions based strictly on the provided handbook text.

Rules:
1. Answer institutional policy questions EXCLUSIVELY from the retrieved handbook context below.
2. NEVER rely on pretrained knowledge to fill gaps.
3. DO NOT fabricate monetary fines, attendance exceptions, deadlines, contacts, eligibility conditions, or approval procedures.
4. If the retrieved evidence does not establish an answer, explicitly say: "The handbook does not provide enough information to answer reliably."
5. Clearly distinguish a stated policy from an inference.
6. CITE the relevant handbook page numbers for factual policy claims.
7. If a question contains multiple parts, answer each part only when supported by evidence.
8. Preserve the actual wording of policies when they appear to differ across sections, and explain the distinction instead of silently resolving the discrepancy.
9. Do not mistake a retrieved but irrelevant chunk for evidence.
10. Do not invent source quotations or page references.

Context:
{context}
"""),
            ("human", "{question}")
        ])

    def format_docs(self, docs):
        formatted = []
        for d in docs:
            page = d.metadata.get('page', 'Unknown')
            formatted.append(f"[Page {page}]: {d.page_content}")
        return "\n\n".join(formatted)

    def ingest_pdf(self, file_path: str) -> Tuple[int, int]:
        if not self.embeddings:
            raise ValueError("Google API Key is not set. Cannot generate embeddings.")
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        page_count = len(documents)

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        chunks = text_splitter.split_documents(documents)
        chunk_count = len(chunks)

        # Create or update ChromaDB
        self.vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=settings.chroma_db_dir
        )
        return page_count, chunk_count

    def chat(self, question: str) -> Tuple[str, List[Dict[str, Any]]]:
        if not self.llm or not self.embeddings:
            raise ValueError("Google API Key is not set. Cannot process chat.")
        if not self.vector_store:
            raise ValueError("Knowledge base not initialized. Please ingest a handbook first.")

        # Use MultiQueryRetriever for expanded retrieval
        retriever_from_llm = MultiQueryRetriever.from_llm(
            retriever=self.vector_store.as_retriever(search_kwargs={"k": 5}),
            llm=self.llm
        )

        docs = retriever_from_llm.invoke(question)
        
        context_str = self.format_docs(docs)

        chain = (
            {"context": lambda x: context_str, "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

        answer = chain.invoke(question)

        sources = []
        for d in docs:
            sources.append({
                "page": d.metadata.get('page', 0) + 1, # PyPDFLoader pages are 0-indexed, let's make it 1-indexed. Wait, PyPDFLoader gives 0-indexed pages.
                "content": d.page_content
            })

        return answer, sources

rag_pipeline = RAGPipeline()
