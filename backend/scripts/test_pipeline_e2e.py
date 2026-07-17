"""
End-to-end smoke test for the real document processing pipeline.

Runs a document (a real file you provide, or a synthetic one generated on the
fly) through the actual `get_document_pipeline()` factory used in production —
Upload -> Fingerprint -> ... -> OCR -> Layout -> Classification -> Extraction
-> Evidence Graph -> Cross-Validation -> Decision -> Human Review -> Archiving
-- and prints what really happened at each step: no mocks, no fabricated data.

Optionally also runs the multi-agent claim flow (OCR Supervisor + Fraud Agent,
both backed by real engines / a real local LLM via Ollama) on the same file.

Usage:
    poetry run python scripts/test_pipeline_e2e.py                 # synthetic PDF
    poetry run python scripts/test_pipeline_e2e.py path/to/doc.pdf  # your own file
    poetry run python scripts/test_pipeline_e2e.py path/to/doc.jpg --no-agents
"""

import asyncio
import json
import os
import sys

# Add backend directory to sys.path (same convention as scripts/seed_db.py)
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.pipeline import get_document_pipeline
from app.pipeline.core import DocumentContext
from app.engines.base import EngineStatus


CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


def build_synthetic_pdf() -> bytes:
    """A real, valid 2-page PDF with claim-like text, rendered via PyMuPDF."""
    import fitz

    doc = fitz.open()

    page1 = doc.new_page()
    page1.insert_text((50, 72), "CONSTAT AMIABLE D'ACCIDENT")
    page1.insert_text((50, 110), "POLICY NO: FR-20260713")
    page1.insert_text((50, 150), "PLATE: AB-123-CD")
    page1.insert_text((50, 190), "Date of loss: 2026-07-10")
    page1.insert_text((50, 230), "Description: Rear-end collision at a red light.")

    page2 = doc.new_page()
    page2.insert_text((50, 72), "Second vehicle involved:")
    page2.insert_text((50, 110), "PLATE: XY-999-ZZ")
    page2.insert_text((50, 150), "Witness statement attached.")

    return doc.tobytes()


def print_header(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def run_document_pipeline(payload: bytes, filename: str, content_type: str) -> DocumentContext:
    print_header("DOCUMENT PIPELINE (get_document_pipeline())")

    pipeline = get_document_pipeline()
    context = DocumentContext(payload=payload, filename=filename, content_type=content_type)

    result = pipeline.execute(context)

    print(f"\nCompleted steps ({len(result.completed_steps)}):")
    for step in result.completed_steps:
        print(f"  - {step}")

    if result.errors:
        print(f"\nErrors/degradations recorded ({len(result.errors)}):")
        for err in result.errors:
            print(f"  [{err['severity']}] {err['step']}: {err['message']}")
    else:
        print("\nNo errors — every step ran cleanly on real data.")

    print(f"\nPages rendered: {len(result.pages)}")
    for page in result.pages:
        print(f"  - page {page.page_number}: {page.image_uri}")

    print(f"\nDocument type detected: {result.document_type_code}")
    print(f"Extracted entities (extracted_data): {json.dumps(result.extracted_data, indent=2)[:1500]}")

    if "decision" in result.engine_results:
        decision = result.engine_results["decision"].output_data.get("decision_result", {})
        print("\nReal Decision Engine output:")
        print(json.dumps(decision, indent=2, default=str))

    print(f"\nFINAL validation_decision: {result.validation_decision}")

    return result


async def run_agent_flow(image_path: str) -> None:
    print_header("MULTI-AGENT FLOW (OCR Supervisor + Fraud Agent, real LLM)")

    from app.agents.manager import AgentManager

    manager = AgentManager()
    result = await manager.process_claim("SCRIPT-TEST", {"image_path": image_path})

    print(f"\nStatus: {result['status']}")
    for agent_id, agent_result in result["agent_results"].items():
        if agent_result is None:
            print(f"  {agent_id}: SKIPPED")
        else:
            print(f"  {agent_id}: {agent_result['status']} — {agent_result['messages']}")

    fraud_score = result["context"]["metadata"].get("fraud_score")
    print(f"\nFraud score (from a real LLM call, not a keyword match): {fraud_score}")


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    with_agents = "--no-agents" not in sys.argv

    if args:
        file_path = args[0]
        ext = os.path.splitext(file_path)[1].lower()
        content_type = CONTENT_TYPES.get(ext)
        if not content_type:
            print(f"Unsupported extension '{ext}'. Supported: {list(CONTENT_TYPES)}")
            sys.exit(1)
        with open(file_path, "rb") as f:
            payload = f.read()
        filename = os.path.basename(file_path)
        print(f"Using provided file: {file_path}")
    else:
        print("No file provided — generating a synthetic 2-page test PDF.")
        payload = build_synthetic_pdf()
        filename = "synthetic_test_claim.pdf"
        content_type = "application/pdf"

    result = run_document_pipeline(payload, filename, content_type)

    if with_agents:
        page_image_path = None
        if result.pages:
            page_image_path = result.pages[0].image_uri.replace("local://", "")
        if page_image_path and os.path.exists(page_image_path):
            asyncio.run(run_agent_flow(page_image_path))
        else:
            print_header("MULTI-AGENT FLOW")
            print("Skipped: no rendered page image available to feed the agents.")

    print("\nDone.\n")


if __name__ == "__main__":
    main()
