"""Pydantic models for the AI service."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, conlist


class EmbeddingsRequest(BaseModel):
    texts: conlist(str, min_length=1, max_length=64)


class EmbeddingsResponse(BaseModel):
    vectors: List[List[float]]


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: conlist(ChatMessage, min_length=1, max_length=50)
    model: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    usage: dict = Field(default_factory=dict)
