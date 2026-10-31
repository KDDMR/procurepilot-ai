import re
from dataclasses import dataclass
from pathlib import Path

from procurepilot.models import PolicyEvidence, ProcurementRequest

STOP_WORDS = {
    "and",
    "are",
    "for",
    "from",
    "has",
    "have",
    "the",
    "this",
    "with",
    "und",
    "der",
    "die",
    "das",
}


@dataclass(frozen=True)
class PolicyChunk:
    source: str
    section: str
    text: str


class PolicyRetriever:
    """Small, transparent lexical retriever for local policy documents.

    The deterministic implementation keeps the demo runnable without external
    services. It can later be replaced by Azure AI Search without changing the
    agent contract.
    """

    def __init__(self, policy_directory: Path) -> None:
        self._chunks = self._load_chunks(policy_directory)
        if not self._chunks:
            raise ValueError(f"No policy sections found in {policy_directory}")

    @staticmethod
    def _load_chunks(policy_directory: Path) -> list[PolicyChunk]:
        chunks: list[PolicyChunk] = []
        for path in sorted(policy_directory.glob("*.md")):
            section = "Introduction"
            buffer: list[str] = []
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.startswith("## "):
                    if buffer:
                        chunks.append(PolicyChunk(path.name, section, " ".join(buffer).strip()))
                    section = line.removeprefix("## ").strip()
                    buffer = []
                elif line and not line.startswith("# "):
                    buffer.append(line.strip())
            if buffer:
                chunks.append(PolicyChunk(path.name, section, " ".join(buffer).strip()))
        return [chunk for chunk in chunks if chunk.text]

    @staticmethod
    def _terms(text: str) -> set[str]:
        return {
            term
            for term in re.findall(r"[a-zA-Z0-9]+", text.lower())
            if len(term) > 2 and term not in STOP_WORDS
        }

    def retrieve(self, request: ProcurementRequest, limit: int = 4) -> list[PolicyEvidence]:
        query = (
            f"{request.description} {request.department} {request.data_classification} "
            f"personal data {request.contains_personal_data} single source {request.single_source} "
            f"urgent {request.urgent} amount {request.amount_eur}"
        )
        query_terms = self._terms(query)
        scored: list[tuple[float, PolicyChunk]] = []
        for chunk in self._chunks:
            section_terms = self._terms(chunk.section)
            text_terms = self._terms(chunk.text)
            overlap = len(query_terms & text_terms)
            heading_overlap = len(query_terms & section_terms)
            score = (overlap + 2 * heading_overlap) / max(len(query_terms), 1)
            scored.append((score, chunk))

        selected = sorted(scored, key=lambda item: item[0], reverse=True)[:limit]
        return [
            PolicyEvidence(
                source=chunk.source,
                section=chunk.section,
                excerpt=chunk.text[:420],
                relevance=min(round(score, 3), 1.0),
            )
            for score, chunk in selected
        ]
