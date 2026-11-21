from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.postgres import Base


class Notebook(Base):
    """A Smriti notebook: one set of files that chat is allowed to use."""

    __tablename__ = "notebooks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    documents: Mapped[list["Document"]] = relationship(
        back_populates="notebook",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Document(Base):
    """One uploaded file and how it was split for retrieval."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    notebook_id: Mapped[int] = mapped_column(
        ForeignKey("notebooks.id", ondelete="CASCADE"),
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(255))
    chunking_strategy: Mapped[str] = mapped_column(String(50))
    chunk_count: Mapped[int] = mapped_column(Integer)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    notebook: Mapped[Notebook] = relationship(back_populates="documents")
