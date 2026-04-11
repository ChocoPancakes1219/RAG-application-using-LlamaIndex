from __future__ import annotations

import importlib.util
from pathlib import Path


RUNNER_PATH = Path(
    "/Users/mikemin/Development/MyProjects/SaaS/min-minisaas-airag/qa/airag_qa_client/runner.py"
)
SPEC = importlib.util.spec_from_file_location("airag_qa_runner", RUNNER_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_evaluate_query_accepts_positive_matches():
    payload = {
        "response": "Cruzeiro/MG finished rank 1 with 100 points.",
        "citations": [
            {
                "filename": "league_table_2003.txt",
                "snippet": "2003;1;Cruzeiro/MG;100;31;7;8",
            }
        ],
    }
    scenario = {
        "expected_keywords": ["cruzeiro/mg", "100"],
        "expected_answer_contains": ["cruzeiro/mg", "100"],
        "expected_filenames": ["league_table_2003.txt"],
        "min_citations": 1,
    }

    result = MODULE.evaluate_query(payload, scenario)

    assert result["passed"] is True
    assert result["citation_count_ok"] is True


def test_evaluate_query_rejects_forbidden_phrase():
    payload = {
        "response": "Santos/SP finished rank 2 with 87 points.",
        "citations": [
            {
                "filename": "league_table_2003.txt",
                "snippet": "2003;2;Santos/SP;87;25;12;9",
            }
        ],
    }
    scenario = {
        "expected_answer_contains": ["santos/sp", "87"],
        "expected_answer_not_contains": ["cruzeiro/mg", "rank 1"],
        "expected_filenames": ["league_table_2003.txt"],
        "min_citations": 1,
    }

    result = MODULE.evaluate_query(payload, scenario)

    assert result["passed"] is True
    assert result["answer_negative_hits"]["cruzeiro/mg"] is False
    assert result["answer_negative_hits"]["rank 1"] is False
