"""
Streamlit UI entry point for the IBD/UC RAG prototype.

Run with:  streamlit run streamlit_app.py

Local, single-user, informational prototype only. No production auth, no
deployment configuration, no external database, no cloud service
integration. Retrieval and answer composition are fully deterministic and
require zero model/API calls by default (see .env.example /
ENABLE_MODEL_CALLS).
"""

from __future__ import annotations

import streamlit as st

from app.evidence_loader import get_topic_vocabulary, load_evidence_package
from app.retrieval import build_retriever
from app.subagents import build_extended_workflow, run_extended_query
from app.workflow import build_workflow, run_query
from memory import UserPreferenceMemory, clear_all_memory
from memory.session_memory import get_streamlit_session_memory

st.set_page_config(page_title="IBD/UC Evidence Prototype", page_icon=None, layout="wide")


@st.cache_resource
def get_pipeline():
    package = load_evidence_package()
    retriever = build_retriever(package)
    graph = build_workflow(package, retriever)
    extended_graph = build_extended_workflow(package, retriever)
    topics = get_topic_vocabulary(package)
    return package, retriever, graph, extended_graph, topics


package, retriever, graph, extended_graph, topic_vocabulary = get_pipeline()

session_memory = get_streamlit_session_memory()

if "_preference_memory" not in st.session_state:
    st.session_state["_preference_memory"] = UserPreferenceMemory()
preference_memory: UserPreferenceMemory = st.session_state["_preference_memory"]

# --- persistent notices -------------------------------------------------

st.warning(
    "**Informational prototype only** -- not a medical device, not a substitute for "
    "professional medical advice, diagnosis, or treatment. All evidence in this tool is "
    "**pending human clinical review** and has not been clinically approved."
)

with st.sidebar:
    st.markdown("### About this prototype")
    st.info(
        "This is a local, non-production prototype that surfaces reviewed evidence for "
        "**ulcerative colitis (UC)** only. It does not diagnose, predict flares, "
        "recommend medication changes, or generate individualized diet plans."
    )
    st.markdown(
        f"**UC-eligible evidence set:** currently **{len(package.uc_eligible_claims)} claims** "
        "(a small, fixed set -- see README for details)."
    )
    st.markdown("**Evidence status:** pending human review.")
    st.markdown("---")
    st.markdown("### Filters")
    topic_choice = st.selectbox(
        "Topic filter (optional)",
        options=["(any)"] + topic_vocabulary,
        index=0,
    )
    st.selectbox(
        "Disease filter",
        options=["ulcerative_colitis"],
        index=0,
        disabled=True,
        help="This is a UC-only tool. Crohn's disease is not selectable here.",
    )

    st.markdown("---")
    st.markdown("### Preferences")
    st.caption("Saved locally (not clinical data); see 'Clear my data' below to reset.")
    length_options = ["short", "standard", "detailed"]
    chosen_length = st.selectbox(
        "Preferred answer length",
        options=length_options,
        index=length_options.index(preference_memory.answer_length),
    )
    if chosen_length != preference_memory.answer_length:
        preference_memory.set_answer_length(chosen_length)

    chosen_expanded = st.checkbox(
        "Expand citations by default",
        value=preference_memory.citations_expanded_default,
    )
    if chosen_expanded != preference_memory.citations_expanded_default:
        preference_memory.set_citations_expanded_default(chosen_expanded)

    st.markdown("---")
    if st.button("Clear my data"):
        clear_all_memory(session_memory, preference_memory)
        st.success("Session memory and saved preferences have been cleared.")

st.title("IBD / UC Evidence Prototype")
st.caption("Local prototype -- deterministic, keyword/BM25 retrieval over a reviewed UC evidence set.")

query = st.text_input(
    "Ask a question about ulcerative colitis nutrition/lifestyle evidence",
    placeholder="e.g. What does the evidence say about fibre in ulcerative colitis?",
)

submitted = st.button("Ask")

if submitted and query.strip():
    selected_topic = None if topic_choice == "(any)" else topic_choice
    result = run_query(graph, query, topic_filter=selected_topic, disease_filter="ulcerative_colitis")

    # Run the extended subagent graph in parallel, purely to populate the
    # Developer / QA panel below -- it never affects the primary
    # user-facing answer, which continues to come from the original,
    # unmodified 8-node ``graph`` above.
    dev_result = run_extended_query(extended_graph, query, topic_filter=selected_topic, disease_filter="ulcerative_colitis")

    session_memory.set_current_question(query)
    session_memory.set_retrieved_claim_ids([c["claimId"] for c in result.get("citations", [])])
    session_memory.add_turn(query, result.get("answer", ""))
    if result.get("status") == "refused":
        session_memory.add_safety_warning(result.get("answer", ""))

    st.markdown("## Answer")
    status = result.get("status")
    if status == "answered":
        st.success(result["answer"])
    elif status == "refused":
        st.error(result["answer"])
    else:
        st.warning(result["answer"])

    if result.get("show_symptom_caveat"):
        st.info(
            "Note: symptoms and measurable intestinal inflammation do not always move "
            "together in ulcerative colitis. This information does not confirm or rule "
            "out active inflammation."
        )

    st.markdown("## Evidence / Citations")
    citations = result.get("citations", [])
    if not citations:
        st.markdown(
            "_No sufficient evidence was retrieved for this query from the reviewed UC "
            "evidence set. This is a distinct state from a real answer -- no claim is "
            "being made either way._"
        )
    else:
        for c in citations:
            with st.expander(
                f"[{c['number']}] {c['sourceTitle']}", expanded=preference_memory.citations_expanded_default
            ):
                st.markdown(f"Claim ID: `{c['claimId']}`  |  Evidence level: {c['evidenceLevel']}  |  Confidence: {c['confidence']}")
                st.markdown(f"**Claim:** {c['claimText']}")
                st.markdown(f"**Supporting excerpt:** {c['supportingExcerpt']}")
                st.markdown(f"**Exact locator:** {c['exactLocator']}")
                st.markdown(f"**Source URL:** {c['sourceUrl']}")
                st.markdown(f"**Limitations:** {c['limitations']}")
                st.markdown(f"**Applicability limitations:** {c['applicabilityLimitations']}")

    st.markdown("## Limitations and Safety")
    st.markdown(
        "- This tool only surfaces evidence explicitly reviewed as applicable to "
        "ulcerative colitis (substring match on `conditionApplicability`).\n"
        "- Crohn's-disease-only evidence is never used to answer UC questions.\n"
        "- The reviewed UC-eligible evidence set is currently small (5 claims); most "
        "topics are **not** covered and will correctly return an unsupported-topic "
        "message rather than a fabricated answer.\n"
        "- This tool does not diagnose, predict flares, recommend medication changes, "
        "or produce individualized diet plans.\n"
        "- All evidence is pending human clinical review."
    )

    with st.expander("Developer / QA panel (advanced)", expanded=False):
        st.caption(
            "Diagnostic detail from the extended subagent graph for the most recent query. "
            "This panel is additive and does not change the answer shown above."
        )
        st.markdown("**Node/step sequence taken:**")
        st.code(" -> ".join(dev_result.get("visited_nodes", [])))

        st.markdown("**Subagent decisions/outputs:**")
        for step in dev_result.get("trace", []):
            st.markdown(f"- `{step['node']}`: {step['output']}")

        st.markdown("**Retrieved claim IDs:**")
        st.write([c.claim_id for c in dev_result.get("candidate_claims", [])])

        st.markdown("**Source IDs used:**")
        used_claim_ids = {c["claimId"] for c in dev_result.get("citations", [])}
        st.write(sorted({c["sourceId"] for c in package.all_claims if c["claimId"] in used_claim_ids}))

        st.markdown("**Citation Verifier result:**")
        st.json(dev_result.get("citation_verifier_result", {}))

        st.markdown("**Safety Critic result:**")
        st.json(dev_result.get("safety_critic_result", {}))

        st.markdown("**Gap Detector result:**")
        st.json({"is_evidence_gap": dev_result.get("is_evidence_gap"), "known_unsupported": dev_result.get("known_unsupported")})

        st.markdown("**QA Agent structured pass/fail report:**")
        st.json(dev_result.get("qa_report", {}))

        st.markdown("**Session memory (this session only, never persisted to disk):**")
        st.json(session_memory.as_dict())
elif submitted:
    st.warning("Please enter a question.")

st.markdown("---")
st.caption(
    "Informational prototype only. Evidence pending human review. Not for clinical use."
)
