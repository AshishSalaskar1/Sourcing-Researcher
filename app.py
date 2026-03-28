import asyncio
import logging
import os
import time

import httpx
import streamlit as st
from dotenv import load_dotenv

from agents import USAGE_LIMITS, OrchestratorDeps, orchestrator

load_dotenv()
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("supply_risk_radar.app")

st.set_page_config(page_title="Supply Risk Radar", page_icon="🔍", layout="wide")
st.title("🔍 Supply Risk Radar")
st.caption("AI-powered supply chain risk analysis using public data")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask about supply risks for any ingredient or commodity..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("🔍 Analyzing supply chain risks...", expanded=True) as status:
            st.write("Starting multi-agent analysis...")

            async def run_analysis():
                model_name = os.environ.get("AZURE_OPENAI_MODEL", "gpt-4o")
                logger.info("Starting analysis with model azure:%s", model_name)
                async with httpx.AsyncClient(timeout=60) as client:
                    return await orchestrator.run(
                        prompt,
                        model=f"azure:{model_name}",
                        deps=OrchestratorDeps(http_client=client),
                        usage_limits=USAGE_LIMITS,
                    )

            try:
                logger.info("Received prompt: %s", prompt[:200])
                start_time = time.perf_counter()
                result = asyncio.run(run_analysis())
                logger.info(
                    "Analysis completed in %.2fs",
                    time.perf_counter() - start_time,
                )
                report = result.output

                for msg_item in result.all_messages():
                    for part in msg_item.parts:
                        if hasattr(part, "tool_name"):
                            st.write(f"✅ {part.tool_name}")

                status.update(label="Analysis complete!", state="complete")
            except Exception as e:
                logger.exception("Analysis failed")
                status.update(label="Analysis failed", state="error")
                st.error(f"{type(e).__name__}: {e}")
                st.stop()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Risk Score", f"{report.overall_risk_score:.1f}/10")
        with col2:
            st.metric("Risk Level", report.risk_level)
        with col3:
            st.metric("Concentration", report.sourcing.concentration_risk)

        st.subheader("Key Insight")
        st.info(report.key_insight)

        st.subheader("Sourcing Analysis")
        st.write(report.sourcing.summary)
        if report.sourcing.primary_regions:
            for region in report.sourcing.primary_regions:
                share = f" ({region.share_percent}%)" if region.share_percent else ""
                st.write(f"- **{region.country}**{share}: {region.notes or ''}")

        st.subheader("Risk Assessment")
        st.write(report.risk_assessment.summary)
        for factor in report.risk_assessment.risk_factors:
            st.write(
                f"- **{factor.domain.title()}** ({factor.score:.1f}/10): {factor.explanation}"
            )

        if report.risk_assessment.cascade_risks:
            st.subheader("⚠️ Cascade Risks")
            for cascade in report.risk_assessment.cascade_risks:
                st.warning(cascade)

        st.subheader("Resilience Recommendations")
        for opt in report.resilience_options:
            with st.expander(
                f"{'⭐' * (6 - opt.priority)} {opt.strategy} ({opt.timeline})"
            ):
                st.write(opt.description)
                st.write(f"**Addresses:** {', '.join(opt.addresses_risks)}")
                st.write(f"**Cost impact:** {opt.cost_impact}")

        if report.sources_used:
            st.subheader("Sources")
            for source in report.sources_used:
                st.write(f"- {source}")

        response_text = (
            f"**{report.commodity} — Risk Score: {report.overall_risk_score:.1f}/10 "
            f"({report.risk_level})**\n\n{report.key_insight}"
        )
        st.session_state.messages.append(
            {"role": "assistant", "content": response_text}
        )
