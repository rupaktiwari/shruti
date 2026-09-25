"""Build the Chroma index from the text files in knowledge_base/."""

from pathlib import Path
import shutil

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


PROJECT_ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_BASE = PROJECT_ROOT / "knowledge_base"
CHROMA_DIRECTORY = PROJECT_ROOT / "chroma_db"
COLLECTION_NAME = "shruti_knowledge"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def main() -> None:
    source_files = sorted(KNOWLEDGE_BASE.glob("*.txt"))
    if not source_files:
        raise SystemExit(f"No .txt files found in {KNOWLEDGE_BASE}")

    documents = [
        Document(
            page_content=path.read_text(encoding="utf-8"),
            metadata={"source": str(path.relative_to(PROJECT_ROOT))},
        )
        for path in source_files
    ]

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(documents)

    # This is a full rebuild, so old/stale vectors cannot remain in the index.
    if CHROMA_DIRECTORY.exists():
        shutil.rmtree(CHROMA_DIRECTORY)

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIRECTORY),
        collection_name=COLLECTION_NAME,
    )

    print(f"Indexed {len(source_files)} files into {CHROMA_DIRECTORY}")
    print(f"Created {len(chunks)} document chunks")


if __name__ == "__main__":
    main()