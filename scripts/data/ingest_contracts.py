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


DATE_PATTERN = re.compile(r"\b(\d{1,2}/\d{1,2}/(?:\d{2}|\d{4}))\b")
CURRENCY_PATTERN = re.compile(r"\(?\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})\)?")
WARRANT_ROW_PATTERN = re.compile(
    r"^(?P<payee>.+?)\s+(?P<date>\d{1,2}/\d{1,2}/(?:\d{2}|\d{4}))\s+\d+\s+\d+\s+(?P<amount>\(?\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})\)?)\b"
)
AP_ROW_PATTERN = re.compile(
    r"^(?P<payment_number>\d{5,})\s+(?P<payee>.+?)\s+(?P<amount>\(?\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})\)?)$"
)
AP_RUN_DATE_PATTERN = re.compile(r"Accounts\s+Payable\s+Run:\s*(\d{1,2}/\d{1,2}/\d{4})", re.IGNORECASE)
MONTH_DATE_PATTERN = re.compile(
    r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|"
    r"Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},\s+\d{4}\b",
    re.IGNORECASE,
)


@dataclass
class RunStats:
    scanned: int = 0
    warrant_docs: int = 0
    agreement_docs: int = 0
    unknown_docs: int = 0
    skipped_empty: int = 0
    skipped_master_no_embedding: int = 0
    payment_rows_extracted: int = 0
    payment_rows_inserted: int = 0
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
    parser = argparse.ArgumentParser(description="Ingest WoodWard contract PDFs into SQLite and LanceDB")
    parser.add_argument(
        "--contracts-dir",
        type=Path,
        default=PROJECT_ROOT / "workspaces" / "VPS-Board-Scraper" / "documents" / "contracts",
    )
    parser.add_argument("--db-path", type=Path, default=PROJECT_ROOT / "data" / "woodward.db")
    parser.add_argument("--lancedb-path", type=Path, default=PROJECT_ROOT / "data" / "lancedb")
    parser.add_argument("--lancedb-table", type=str, default="woodward_contracts")
    parser.add_argument("--embedding-model", type=str, default="text-embedding-3-small")
    parser.add_argument("--chunk-size", type=int, default=1800)
    parser.add_argument("--chunk-overlap", type=int, default=250)
    parser.add_argument(
        "--replace-master-chunks",
        action="store_true",
        help="Delete existing LanceDB chunks for each source file before re-storing.",
    )
    parser.add_argument(
        "--treat-unknown-as-master",
        action="store_true",
        help="Treat unknown-but-textual documents as master agreements for chunk embedding.",
    )
    parser.add_argument("--limit", type=int, default=None)
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


def classify_document(text: str, filename: str) -> str:
    lowered = text.lower()
    file_lower = filename.lower()

    warrant_score = 0
    agreement_score = 0

    if "warrant register" in lowered or "warrant register" in file_lower:
        warrant_score += 3
    if "payee" in lowered and "amount" in lowered:
        warrant_score += 2
    if len(CURRENCY_PATTERN.findall(text)) >= 5:
        warrant_score += 1

    if "agreement" in lowered or "agreement" in file_lower:
        agreement_score += 2
    if "contract" in lowered or "contract" in file_lower:
        agreement_score += 2
    if "terms" in lowered:
        agreement_score += 1
    if any(token in lowered for token in ["board minutes", "committee of the whole", "regular board meeting"]):
        agreement_score += 2
    if any(token in file_lower for token in ["boardminutes", "board_meeting", "committee", "regular_board"]):
        agreement_score += 2

    if warrant_score >= 3 and warrant_score >= agreement_score:
        return "warrant_register"
    if agreement_score >= 3:
        return "master_agreement"
    return "unknown"


def normalize_amount(value: str) -> Optional[float]:
    if not value:
        return None
    cleaned = value.strip().replace("$", "").replace(",", "")
    is_negative = cleaned.startswith("(") and cleaned.endswith(")")
    cleaned = cleaned.strip("()")
    try:
        amount = float(cleaned)
        return -amount if is_negative else amount
    except ValueError:
        return None


def clean_payee(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip(" -:")
    value = re.sub(r"\b\d{1,4}\s*$", "", value).strip()
    return value


def parse_warrant_entries(text: str) -> List[Tuple[Optional[str], str, float, str]]:
    entries: List[Tuple[Optional[str], str, float, str]] = []
    current_ap_run_date: Optional[str] = None
    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line:
            continue

        run_date_match = AP_RUN_DATE_PATTERN.search(line)
        if run_date_match:
            current_ap_run_date = run_date_match.group(1)

        lowered = line.lower()
        if any(
            token in lowered
            for token in [
                "warrant register",
                "fund totals",
                "page total",
                "subtotal",
                "grand total",
                "total all funds",
                "end of report",
                "payee issued",
                "date warrant",
                "vancouver school district",
                "ap check register",
                "payment number payee net payment amount",
                "account amount",
            ]
        ):
            continue

        ap_match = AP_ROW_PATTERN.match(line)
        if ap_match:
            if re.match(r"^\d+\s+[A-Z]\s+\d+", line):
                continue
            payee = clean_payee(ap_match.group("payee"))
            amount = normalize_amount(ap_match.group("amount"))
            if payee and amount is not None:
                entries.append((current_ap_run_date, payee, amount, raw_line.strip()))
            continue

        match = WARRANT_ROW_PATTERN.match(line)
        if match:
            payee = clean_payee(match.group("payee"))
            entry_date = match.group("date")
            amount = normalize_amount(match.group("amount"))
            if payee and amount is not None:
                entries.append((entry_date, payee, amount, raw_line.strip()))
            continue

        amount_match = None
        for candidate in CURRENCY_PATTERN.finditer(line):
            amount_match = candidate
        if not amount_match:
            continue

        amount = normalize_amount(amount_match.group(0))
        if amount is None:
            continue

        line_before_amount = line[: amount_match.start()].strip()
        date_match = None
        for candidate in DATE_PATTERN.finditer(line_before_amount):
            date_match = candidate

        if not date_match:
            continue

        entry_date = date_match.group(1)
        payee = clean_payee(line_before_amount[: date_match.start()])
        if not payee:
            continue

        entries.append((entry_date, payee, amount, raw_line.strip()))

    return entries


def infer_document_date(text: str, filename: str) -> Optional[str]:
    explicit = DATE_PATTERN.search(text)
    if explicit:
        return explicit.group(1)

    month_style = MONTH_DATE_PATTERN.search(text)
    if month_style:
        return month_style.group(0)

    from_name = DATE_PATTERN.search(filename.replace("__", "/").replace("_", "/"))
    if from_name:
        return from_name.group(1)

    return None


def ensure_payments_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_file TEXT NOT NULL,
            source_path TEXT NOT NULL,
            document_date TEXT,
            entry_date TEXT,
            payee TEXT NOT NULL,
            amount REAL NOT NULL,
            raw_line TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_file, entry_date, payee, amount)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_payments_payee
        ON payments (payee)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_payments_entry_date
        ON payments (entry_date)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_payments_source_file
        ON payments (source_file)
        """
    )
    conn.commit()


def insert_payment_rows(
    conn: sqlite3.Connection,
    source_file: str,
    source_path: str,
    document_date: Optional[str],
    rows: Sequence[Tuple[Optional[str], str, float, str]],
) -> int:
    inserted = 0
    for entry_date, payee, amount, raw_line in rows:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO payments
            (source_file, source_path, document_date, entry_date, payee, amount, raw_line)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (source_file, source_path, document_date, entry_date, payee, amount, raw_line),
        )
        if cursor.rowcount > 0:
            inserted += 1
    conn.commit()
    return inserted


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
    replace_existing: bool,
) -> Tuple[int, int]:
    chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    if not chunks:
        return 0, 0

    source_document_id = pdf_path.stem
    if replace_existing:
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
            "document_type": "master_agreement",
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

    contracts_dir: Path = args.contracts_dir
    if not contracts_dir.exists():
        logging.error("Contracts directory not found: %s", contracts_dir)
        return 1

    pdf_paths = sorted(contracts_dir.glob("*.pdf"))
    if args.limit is not None:
        pdf_paths = pdf_paths[: args.limit]

    if not pdf_paths:
        logging.warning("No PDFs found in %s", contracts_dir)
        return 0

    args.db_path.parent.mkdir(parents=True, exist_ok=True)
    args.lancedb_path.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(args.db_path)
    ensure_payments_table(conn)

    stats = RunStats()
    adapter = None
    embedder = None

    embedding_ready = bool(os.environ.get("OPENAI_API_KEY"))
    if not embedding_ready:
        logging.warning("OPENAI_API_KEY not set. Master agreements will be skipped.")

    if LanceDBAdapter is None:
        logging.warning("Could not import LanceDBAdapter. Master agreements will be skipped.")
        embedding_ready = False

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
            logging.warning("Could not initialize embedding/LanceDB stack: %s", exc)
            embedding_ready = False
            embedder = None
            adapter = None

    try:
        for pdf_path in pdf_paths:
            stats.scanned += 1
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

            doc_type = classify_document(text, pdf_path.name)
            if doc_type == "unknown" and args.treat_unknown_as_master:
                doc_type = "master_agreement"
            if doc_type == "warrant_register":
                stats.warrant_docs += 1
                rows = parse_warrant_entries(text)
                stats.payment_rows_extracted += len(rows)
                if rows:
                    doc_date = infer_document_date(text, pdf_path.name)
                    inserted = insert_payment_rows(
                        conn=conn,
                        source_file=pdf_path.name,
                        source_path=str(pdf_path),
                        document_date=doc_date,
                        rows=rows,
                    )
                    stats.payment_rows_inserted += inserted
                    logging.info(
                        "Warrant entries extracted=%d inserted=%d for %s",
                        len(rows),
                        inserted,
                        pdf_path.name,
                    )
                else:
                    logging.warning("No warrant rows parsed for %s", pdf_path.name)

            elif doc_type == "master_agreement":
                stats.agreement_docs += 1
                if not embedding_ready or adapter is None or embedder is None:
                    stats.skipped_master_no_embedding += 1
                    logging.warning(
                        "Skipping master agreement (embedding not configured): %s",
                        pdf_path.name,
                    )
                    continue

                try:
                    attempted, stored = await store_master_agreement(
                        adapter=adapter,
                        embedder=embedder,
                        pdf_path=pdf_path,
                        text=text,
                        chunk_size=args.chunk_size,
                        chunk_overlap=args.chunk_overlap,
                        replace_existing=args.replace_master_chunks,
                    )
                    stats.lancedb_chunks_attempted += attempted
                    stats.lancedb_chunks_stored += stored
                    logging.info(
                        "Master chunks attempted=%d stored=%d for %s",
                        attempted,
                        stored,
                        pdf_path.name,
                    )
                except Exception as exc:
                    logging.warning("Failed to store master agreement %s: %s", pdf_path.name, exc)

            else:
                stats.unknown_docs += 1
                logging.info("Unclassified document type for %s", pdf_path.name)

    finally:
        conn.close()
        if adapter is not None:
            try:
                await adapter.disconnect()
            except Exception:
                pass

    logging.info("--- Ingestion Summary ---")
    logging.info("PDFs scanned: %d", stats.scanned)
    logging.info("Warrant registers: %d", stats.warrant_docs)
    logging.info("Master agreements: %d", stats.agreement_docs)
    logging.info("Unknown docs: %d", stats.unknown_docs)
    logging.info("Skipped empty/scanned: %d", stats.skipped_empty)
    logging.info("Skipped agreements (no embedding): %d", stats.skipped_master_no_embedding)
    logging.info("Payment rows extracted: %d", stats.payment_rows_extracted)
    logging.info("Payment rows inserted: %d", stats.payment_rows_inserted)
    logging.info("LanceDB chunks attempted: %d", stats.lancedb_chunks_attempted)
    logging.info("LanceDB chunks stored: %d", stats.lancedb_chunks_stored)

    return 0


def main() -> None:
    args = parse_args()
    exit_code = asyncio.run(run(args))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
