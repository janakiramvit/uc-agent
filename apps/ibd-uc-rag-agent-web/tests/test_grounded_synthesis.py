"""Grounded LLM synthesis: proves the final answer text actually comes
from the LLM call (not a deterministic template) AND that the LLM is
handed the real retrieved evidence to ground on -- not just the bare
question."""

from unittest.mock import MagicMock, patch

from agent_core.graph_v2 import run_graph_v2
from agent_core.llm_synthesizer import _format_evidence_block, synthesize_with_llm


def test_format_evidence_block_includes_real_claim_text(retriever):
    verified = retriever.retrieve(query="fibre", topic_filter="fibre")
    block = _format_evidence_block(verified)
    for claim in verified:
        assert claim.claim_id in block
        assert claim.claim_text in block


def test_synthesize_with_llm_sends_evidence_and_returns_model_text(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")

    fake_response = MagicMock()
    fake_response.content = "[1] This is the model-generated grounded answer."
    fake_chat_model = MagicMock()
    fake_chat_model.invoke.return_value = fake_response

    verified = [
        type(
            "C",
            (),
            {
                "claim_id": "CLM-014",
                "claim_text": "Fibre intake was associated with improved outcomes.",
            },
        )()
    ]

    with patch("agent_core.llm_synthesizer._resolve_chat_model", return_value=(fake_chat_model, "anthropic", "claude-sonnet-4-5")):
        result = synthesize_with_llm("Is fibre good for UC?", verified)

    # The answer returned is exactly what the model produced -- not a template.
    assert result.text == "[1] This is the model-generated grounded answer."
    assert result.provider == "anthropic"

    # The evidence text was actually handed to the model, not just the question.
    sent_messages = fake_chat_model.invoke.call_args[0][0]
    sent_text = " ".join(m.content for m in sent_messages)
    assert "CLM-014" in sent_text
    assert "Fibre intake was associated with improved outcomes." in sent_text


def test_full_graph_final_answer_is_the_llm_output_verbatim(graph):
    from agent_core.llm_synthesizer import LLMResult

    model_text = "[1] The evidence reports a fibre association with UC outcomes, per the retrieved claim."
    good_llm = LLMResult(text=model_text, provider="anthropic", model="claude-sonnet-4-5")

    with patch("agent_core.graph_v2.synthesize_with_llm", return_value=good_llm):
        result = run_graph_v2(graph, "Is fibre good for UC?")

    assert result["status"] == "answered"
    assert result["answer"] == model_text  # not a deterministic template rewrite
    assert result["llm_provider"] == "anthropic"
    assert len(result["citations"]) > 0
