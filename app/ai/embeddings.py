"""Utility helpers for handling content embeddings."""

from __future__ import annotations

import math
from typing import Any, Dict, List

from sqlalchemy import JSON, Column, Index, Integer, String
from sqlalchemy.orm import Session

from app.core.database import Base


class ContentEmbedding(Base):
    __tablename__ = "content_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    namespace = Column(String(50), nullable=False, index=True)
    ref_id = Column(String(100), nullable=False, index=True)
    title = Column(String(200), nullable=True)
    meta = Column(JSON, nullable=True)
    embedding = Column(JSON, nullable=False)

    __table_args__ = (
        Index(
            "ix_content_embeddings_namespace_ref", "namespace", "ref_id", unique=True
        ),
    )


def upsert_embedding(
    db: Session,
    namespace: str,
    ref_id: str,
    title: str,
    metadata: Dict[str, Any] | None,
    vector: List[float],
) -> ContentEmbedding:
    obj = (
        db.query(ContentEmbedding).filter_by(namespace=namespace, ref_id=ref_id).first()
    )
    if obj:
        obj.title = title
        obj.meta = metadata
        obj.embedding = vector
    else:
        obj = ContentEmbedding(
            namespace=namespace,
            ref_id=ref_id,
            title=title,
            meta=metadata,
            embedding=vector,
        )
        db.add(obj)
    db.commit()
    return obj


def _cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def search_similar(
    db: Session, namespace: str, vector: List[float], k: int = 5
) -> List[Dict[str, Any]]:
    items = db.query(ContentEmbedding).filter_by(namespace=namespace).all()
    scored = []
    for item in items:
        score = _cosine(vector, item.embedding)
        scored.append((score, item))
    scored.sort(key=lambda s: s[0], reverse=True)
    result = []
    for score, item in scored[:k]:
        result.append(
            {
                "ref_id": item.ref_id,
                "title": item.title,
                "score": score,
                "metadata": item.meta,
            }
        )
    return result


def ensure_seed_embeddings(db: Session) -> None:
    """Populate the table with a minimal seed if empty."""
    if not db.query(ContentEmbedding).first():
        upsert_embedding(db, "routine", "seed", "Seed", {}, [0.1, 0.2, 0.3])
