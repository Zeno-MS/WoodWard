import argparse
import asyncio
import logging
import os
import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import pdfplumber

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CICERO_CLONE_ROOT = PROJECT_ROOT / "workspaces" / "Cicero_Clone"
if str(CICERO_CLONE_ROOT) not in sys.path:
    sys.path.insert(0, str(CICERO_CLONE_ROOT))

try:
    from src.adapters.lancedb import LanceDBAdapter
except Exception:
    LanceDBAdapter = None


@dataclass
class RunStats:
    scanned: int = 0
    skipped_warrant: int = 0
    agreement_docs: int = 0
    unknown_docs: int = 0
    skipped_empty: int = 0
    lancedb_chunks_attempted: int = 0
    lancedb_chunks_stored: int = 0


class EmbeddingClient:
    def __init__(self, model: str):
        from openai import AsyncOpenAI

        self.model = model
        self.client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    async def embed_texts(self, texts: Sequence[str], batch_size: int = 64) -> List[List[float]]:
        vectors: List[List[float]] = []
        for idx in range(0, len(texts), batch_size):
            batch = list(texts[idx : idx + batch_size])
            response = await self.client.embeddings.create(model=self.model, input=batch)
            vectors.extend(item.embedding for item in response.data)
        return vectors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest WoodWard contract MSAs into LanceDB")
    parser.add_argument(
        "--docs-dir",
        type=Path,
        required=True,
    )
    parser.add_argument("--lancedb-path", type=Path, default=PROJECT_ROOT / "data" / "lancedb")
    parser.add_argument("--lancedb-table", type=str, default="woodward_contracts")
    parser.add_argument("--embedding-model", type=str, default="text-embedding-ada-002") # Match the 1536 dim
    parser.add_argument("--chunk-size", type=int, default=1800)
    parser.add_argument("--chunk-overlap", type=int, default=250)
    parser.add_argument("--log-level", type=str, default="INFO")
    return parser.parse_args()


def extract_pdf_text(pdf_path: Path) -> str:
    parts: List[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if text:
                parts.append(text)
    return "\n".join(parts).strip()


def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    normalized = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not normalized:
        return []

    chunks: List[str] = []
    start = 0
    length = len(normalized)

    while start < length:
        end = min(start + chunk_size, length)
        if end < length:
            split_hint = normalized.rfind("\n\n", start, end)
            if split_hint > start + int(chunk_size * 0.5):
                end = split_hint
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= length:
            break

        start = max(0, end - chunk_overlap)

    return chunks


async def store_master_agreement(
    adapter,
    embedder: EmbeddingClient,
    pdf_path: Path,
    text: str,
    chunk_size: int,
    chunk_overlap: int,
) -> Tuple[int, int]:
    chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    if not chunks:
        return 0, 0

    source_document_id = pdf_path.stem
    safe_source_id = source_document_id.replace("'", "''")
    await adapter.table.delete(f"source_document_id = '{safe_source_id}'")

    embeddings = await embedder.embed_texts(chunks)
    items = []
    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        citation_key = f"{pdf_path.name}#chunk-{idx}"
        metadata = {
            "chunk_index": idx,
            "source_file": pdf_path.name,
            "source_path": str(pdf_path),
            "document_type": "board_document",
        }
        items.append(
            {
                "content": chunk,
                "embedding": embedding,
                "source_document_id": source_document_id,
                "citation_key": citation_key,
                "metadata": metadata,
                "workspace_id": "woodward_contracts",
            }
        )

    results = await adapter.store_batch(items, batch_size=64)
    stored = sum(1 for result in results if result.success)
    return len(items), stored


async def run(args: argparse.Namespace) -> int:
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(levelname)s | %(message)s",
    )

    if not args.docs_dir.exists():
        logging.error("Directory not found: %s", args.docs_dir)
        return 1

    pdf_paths = sorted(args.docs_dir.rglob("*.pdf"))

    if not pdf_paths:
        logging.warning("No PDFs found in %s", args.docs_dir)
        return 0

    args.lancedb_path.mkdir(parents=True, exist_ok=True)

    stats = RunStats()
    adapter = None
    embedder = None

    embedding_ready = bool(os.environ.get("OPENAI_API_KEY"))
    if not embedding_ready:
        logging.error("OPENAI_API_KEY not set.")
        return 1

    if LanceDBAdapter is None:
        logging.error("Could not import LanceDBAdapter. Master agreements will be skipped.")
        return 1

    if embedding_ready:
        try:
            embedder = EmbeddingClient(model=args.embedding_model)
            adapter = LanceDBAdapter(
                db_path=str(args.lancedb_path),
                table_name=args.lancedb_table,
                embedding_dim=1536,
                distance_metric="cosine",
            )
            await adapter.connect()
        except Exception as exc:
            logging.error("Could not initialize embedding/LanceDB stack: %s", exc)
            return 1

    try:
        for pdf_path in pdf_paths:
            stats.scanned += 1
            
            # CRITICAL OPTIMIZATION: Skip warrant registers entirely.
            if "warrant" in pdf_path.name.lower() or "register" in pdf_path.name.lower():
                stats.skipped_warrant += 1
                continue

            logging.info("Processing %s", pdf_path.name)
            try:
                text = extract_pdf_text(pdf_path)
            except Exception as exc:
                logging.warning("Failed to read PDF %s: %s", pdf_path.name, exc)
                continue

            if not text.strip():
                stats.skipped_empty += 1
                logging.warning("No extractable text (possibly scanned image): %s", pdf_path.name)
                continue

            stats.agreement_docs += 1
            try:
                attempted, stored = await store_master_agreement(
                    adapter=adapter,
                    embedder=embedder,
                    pdf_path=pdf_path,
                    text=text,
                    chunk_size=args.chunk_size,
                    chunk_overlap=args.chunk_overlap,
                )
                stats.lancedb_chunks_attempted += attempted
                stats.lancedb_chunks_stored += stored
                logging.info(
                    "LanceDB chunks attempted=%d stored=%d for %s",
                    attempted,
                    stored,
                    pdf_path.name,
                )
            except Exception as exc:
                logging.warning("Failed to store master agreement %s: %s", pdf_path.name, exc)

    finally:
        if adapter is not None:
            try:
                await adapter.disconnect()
            except Exception:
                pass

    logging.info("--- Ingestion Summary ---")
    logging.info("PDFs scanned: %d", stats.scanned)
    logging.info("Warrant registers skipped: %d", stats.skipped_warrant)
    logging.info("Agreements processed: %d", stats.agreement_docs)
    logging.info("Skipped empty/scanned: %d", stats.skipped_empty)
    logging.info("LanceDB chunks attempted: %d", stats.lancedb_chunks_attempted)
    logging.info("LanceDB chunks stored: %d", stats.lancedb_chunks_stored)

    return 0


def main() -> None:
    args = parse_args()
    exit_code = asyncio.run(run(args))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
