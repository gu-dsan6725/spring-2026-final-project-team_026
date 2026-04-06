import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from dotenv import load_dotenv

from langchain_community.chat_models import ChatLiteLLM
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate


class DirectoryRAGAgent:
    """
    A reusable RAG agent for loading a code/document directory,
    building a FAISS vector store, and answering questions over it.
    This is the wrapped class version of dir_loader.ipynb code for further construction of 
    Debt Detector Agent and further agent.

    Import this class for rag agent
    """

    def __init__(
        self,
        directory_path: str,
        model_id: str = "groq/llama-3.1-8b-instant",
        embedding_model_name: str = "all-MiniLM-L6-v2",
        glob_patterns: Optional[List[str]] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        temperature: float = 0,
        default_k: int = 5,
        use_mmr: bool = False,
    ) -> None:
        load_dotenv()

        self.directory_path = directory_path
        self.model_id = model_id
        self.embedding_model_name = embedding_model_name
        self.glob_patterns = glob_patterns or ["**/*.txt", "**/*.md", "**/*.py", "**/*.sh"]
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.temperature = temperature
        self.default_k = default_k
        self.use_mmr = use_mmr

        self.logger = logging.getLogger(self.__class__.__name__)

        self.llm = None
        self.embeddings = None
        self.documents = None
        self.splits = None
        self.vectorstore = None
        self.retriever = None
        self.prompt = None
        self.question_answer_chain = None
        self.rag_chain = None

        self._setup_llm()
        self._setup_prompt()

    def _setup_llm(self) -> None:
        """Initialize the LLM."""
        if os.getenv("GROQ_API_KEY"):
            self.logger.info("GROQ_API_KEY is set")

        self.llm = ChatLiteLLM(
            model=self.model_id,
            temperature=self.temperature
        )
        self.logger.info(f"Using model: {self.model_id}")

    def _setup_prompt(self) -> None:
        """Initialize the prompt template."""
        system_prompt = (
            "You are an agent aiming to solve tech debt problems in the directory you loaded. "
            "The directory may contain outdated code. "
            "Use the following retrieved context to understand the codebase. "
            "If you do not know the answer, say that you do not know.\n\n"
            "{context}"
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{input}"),
            ]
        )

    def load_documents(self) -> None:
        """Load documents from the target directory."""
        all_docs = []

        for pattern in self.glob_patterns:
            loader = DirectoryLoader(self.directory_path, glob=pattern)
            docs = loader.load()
            all_docs.extend(docs)

        self.documents = all_docs
        self.logger.info(f"Loaded {len(self.documents)} documents from {self.directory_path}")

    def split_documents(self) -> None:
        """Split loaded documents into chunks."""
        if self.documents is None:
            raise ValueError("Documents not loaded. Call load_documents() first.")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        self.splits = text_splitter.split_documents(self.documents)
        self.logger.info(f"Split into {len(self.splits)} chunks")

    def build_vectorstore(self) -> None:
        """Build FAISS vectorstore from split documents."""
        if self.splits is None:
            raise ValueError("Document splits not ready. Call split_documents() first.")

        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.embedding_model_name
        )
        self.logger.info("Embeddings model loaded successfully")

        self.vectorstore = FAISS.from_documents(
            documents=self.splits,
            embedding=self.embeddings
        )
        self.logger.info("FAISS vectorstore built successfully")

    def build_retriever(self, k: Optional[int] = None, use_mmr: Optional[bool] = None) -> None:
        """Build retriever from vectorstore."""
        if self.vectorstore is None:
            raise ValueError("Vectorstore not built. Call build_vectorstore() first.")

        k = k if k is not None else self.default_k
        use_mmr = use_mmr if use_mmr is not None else self.use_mmr

        if use_mmr:
            self.retriever = self.vectorstore.as_retriever(
                search_type="mmr",
                search_kwargs={"k": k}
            )
        else:
            self.retriever = self.vectorstore.as_retriever(
                search_kwargs={"k": k}
            )

        self.logger.info(f"Retriever created with k={k}, use_mmr={use_mmr}")

    def build_chain(self) -> None:
        """Build the retrieval QA chain."""
        if self.retriever is None:
            raise ValueError("Retriever not built. Call build_retriever() first.")

        self.question_answer_chain = create_stuff_documents_chain(self.llm, self.prompt)
        self.rag_chain = create_retrieval_chain(self.retriever, self.question_answer_chain)
        self.logger.info("RAG chain built successfully")

    def initialize(self, k: Optional[int] = None, use_mmr: Optional[bool] = None) -> None:
        """Run the full pipeline from document loading to chain creation."""
        self.load_documents()
        self.split_documents()
        self.build_vectorstore()
        self.build_retriever(k=k, use_mmr=use_mmr)
        self.build_chain()

    def ask(self, question: str) -> str:
        """Ask a question against the indexed directory."""
        if self.rag_chain is None:
            raise ValueError("RAG chain not initialized. Call initialize() first.")

        result = self.rag_chain.invoke({"input": question})
        return result["answer"]

    def retrieve_only(self, query: str) -> List[Any]:
        """Return retrieved documents without calling the LLM."""
        if self.retriever is None:
            raise ValueError("Retriever not initialized. Call initialize() first.")

        return self.retriever.invoke(query)

    def summarize_directory(self) -> str:
        """Convenience method to summarize the directory."""
        return self.ask("Summarize the directory. What is it about?")

    def inspect_file(self, question_prompt, filename: str) -> str:
        """Convenience method to check outdated code or packages in a target file.
            Always start with "In {filename},"
        """
        return self.ask(
            f"In {filename}" + question_prompt
        )

    def rebuild_retriever(self, k: int = 5, use_mmr: bool = False) -> None:
        """Change retriever strategy without rebuilding embeddings/vectorstore."""
        self.build_retriever(k=k, use_mmr=use_mmr)
        self.build_chain()