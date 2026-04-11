from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from uuid import uuid4

import httpx
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
QA_DIR = Path(__file__).resolve().parent
REPORTS_DIR = QA_DIR / "reports"
load_dotenv(QA_DIR / ".env.qa")


def load_scenario(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_query(query_payload: dict, scenario: dict) -> dict:
    expected_keywords = scenario.get("expected_keywords", [])
    expected_answer_contains = scenario.get("expected_answer_contains", [])
    expected_answer_not_contains = scenario.get("expected_answer_not_contains", [])
    expected_filenames = scenario.get("expected_filenames", [])
    min_citations = int(scenario.get("min_citations", 0))

    answer_text = (query_payload.get("response") or "").lower()
    citations = query_payload.get("citations", []) or []
    citation_text = " ".join((item.get("snippet") or "").lower() for item in citations)
    citation_filenames = [item.get("filename") for item in citations]

    keyword_hits = {
        keyword: (keyword.lower() in answer_text or keyword.lower() in citation_text)
        for keyword in expected_keywords
    }
    answer_hits = {
        phrase: (phrase.lower() in answer_text)
        for phrase in expected_answer_contains
    }
    answer_negative_hits = {
        phrase: (phrase.lower() in answer_text)
        for phrase in expected_answer_not_contains
    }
    filename_hits = {
        filename: (filename in citation_filenames)
        for filename in expected_filenames
    }
    citation_count_ok = len(citations) >= min_citations

    passed = all(
        [
            all(keyword_hits.values()) if keyword_hits else True,
            all(answer_hits.values()) if answer_hits else True,
            not any(answer_negative_hits.values()) if answer_negative_hits else True,
            all(filename_hits.values()) if filename_hits else True,
            citation_count_ok,
        ]
    )

    return {
        "expected_keywords": expected_keywords,
        "keyword_hits": keyword_hits,
        "expected_answer_contains": expected_answer_contains,
        "answer_hits": answer_hits,
        "expected_answer_not_contains": expected_answer_not_contains,
        "answer_negative_hits": answer_negative_hits,
        "expected_filenames": expected_filenames,
        "filename_hits": filename_hits,
        "min_citations": min_citations,
        "actual_citations": len(citations),
        "citation_count_ok": citation_count_ok,
        "passed": passed,
    }


def run_query_case(
    client: httpx.Client,
    *,
    base_url: str,
    api_key: str,
    user_id: str,
    case: dict,
) -> dict:
    query_response = client.post(
        f"{base_url}/internal/rag/query",
        headers={"X-Internal-API-Key": api_key},
        json={
            "user_id": user_id,
            "query": case["query"],
            "top_k": case.get("top_k", 3),
        },
    )
    query_response.raise_for_status()
    query_payload = query_response.json()
    evaluation = evaluate_query(query_payload, case)
    return {
        "name": case.get("name", case["query"]),
        "query": query_payload,
        "evaluation": evaluation,
    }


def poll_ready(
    client: httpx.Client,
    *,
    base_url: str,
    api_key: str,
    user_id: str,
    document_id: str,
    timeout_seconds: float,
) -> dict:
    deadline = time.time() + timeout_seconds
    last_payload: dict | None = None
    while time.time() < deadline:
        response = client.get(
            f"{base_url}/internal/rag/documents/{document_id}",
            params={"user_id": user_id},
            headers={"X-Internal-API-Key": api_key},
        )
        response.raise_for_status()
        payload = response.json()
        last_payload = payload
        if payload["status"] == "ready":
            return payload
        if payload["status"] == "failed":
            raise RuntimeError(f"ingest failed: {payload}")
        time.sleep(1.0)
    raise TimeoutError(f"document did not reach ready state: {last_payload}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a live AIRAG QA scenario.")
    parser.add_argument(
        "--scenario",
        default="qa/airag_qa_client/scenarios/smoke.json",
        help="Path to scenario JSON file",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=30.0,
        help="Ready polling timeout",
    )
    args = parser.parse_args()

    scenario_path = Path(args.scenario)
    if not scenario_path.is_absolute():
        qa_candidate = (QA_DIR / scenario_path).resolve()
        root_candidate = (ROOT_DIR / scenario_path).resolve()
        scenario_path = qa_candidate if qa_candidate.exists() else root_candidate
    scenario = load_scenario(scenario_path)

    base_url = os.getenv("AIRAG_BASE_URL", "http://127.0.0.1:58777")
    api_key = os.getenv("AIRAG_INTERNAL_API_KEY")
    if not api_key:
        raise RuntimeError(
            "AIRAG_INTERNAL_API_KEY is required. Create qa/airag_qa_client/.env.qa from .env.qa.example."
        )
    user_id = f"qa-{uuid4().hex[:8]}"

    fixture_path = (scenario_path.parent.parent / "fixtures" / scenario["fixture"]).resolve()
    fixture_bytes = fixture_path.read_bytes()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"report-{scenario['name']}-{int(time.time())}.json"

    report: dict = {
        "scenario": scenario["name"],
        "base_url": base_url,
        "user_id": user_id,
        "fixture": str(fixture_path),
    }

    with httpx.Client(timeout=60.0) as client:
        ingest_response = client.post(
            f"{base_url}/internal/rag/documents",
            headers={"X-Internal-API-Key": api_key},
            data={"user_id": user_id},
            files={"files": (fixture_path.name, fixture_bytes, "text/plain")},
        )
        ingest_response.raise_for_status()
        ingest_payload = ingest_response.json()
        report["ingest"] = ingest_payload

        document_id = ingest_payload["items"][0]["document_id"]
        ready_payload = poll_ready(
            client,
            base_url=base_url,
            api_key=api_key,
            user_id=user_id,
            document_id=document_id,
            timeout_seconds=args.timeout_seconds,
        )
        report["ready"] = ready_payload

        cases = scenario.get("cases")
        if cases:
            case_reports = [
                run_query_case(
                    client,
                    base_url=base_url,
                    api_key=api_key,
                    user_id=user_id,
                    case=case,
                )
                for case in cases
            ]
            report["cases"] = case_reports
            report["evaluation"] = {
                "total_cases": len(case_reports),
                "passed_cases": sum(
                    1 for case_report in case_reports if case_report["evaluation"]["passed"]
                ),
                "failed_cases": [
                    case_report["name"]
                    for case_report in case_reports
                    if not case_report["evaluation"]["passed"]
                ],
                "passed": all(case_report["evaluation"]["passed"] for case_report in case_reports),
            }
        else:
            case_report = run_query_case(
                client,
                base_url=base_url,
                api_key=api_key,
                user_id=user_id,
                case=scenario,
            )
            report["query"] = case_report["query"]
            report["evaluation"] = case_report["evaluation"]

        delete_response = client.delete(
            f"{base_url}/internal/rag/documents/{document_id}",
            params={"user_id": user_id},
            headers={"X-Internal-API-Key": api_key},
        )
        report["delete_status_code"] = delete_response.status_code

    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\nreport saved to: {report_path}")
    return 0 if report["evaluation"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
