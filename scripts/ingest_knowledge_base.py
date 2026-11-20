"""Re-index knowledge_base/*.txt into Qdrant. Requires Postgres and Qdrant to be up."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import models  # noqa: F401
from app.db.postgres import Base, engine
from app.services.knowledge_seed import seed_knowledge_base
from app.services.vector_store_service import ensure_collection


def main() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_collection()
    chunks = seed_knowledge_base(force=True)
    print(f"Indexed {chunks} chunks from knowledge_base/")


if __name__ == "__main__":
    main()
