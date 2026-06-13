import os
import time
from datetime import datetime
from typing import Any

from openai import APIConnectionError, APIStatusError, RateLimitError

from src.logger import log

from src.ai.ollama_client import get_ollama_client
from src.ai.openai_client import get_client
from src.utils.performance import PerformanceMetrics, PerformanceTimer


class ReportGenerator:

    REQUIRED_SECTION_HEADERS = (
        "1. GLOBAL CAPITAL FLOW SNAPSHOT",
        "16. CORE INSIGHT",
    )

    @staticmethod
    def generate(prompt: str, market_context: str | dict):
        context_text = market_context["context"] if isinstance(market_context, dict) else market_context
        sources = market_context.get("sources", []) if isinstance(market_context, dict) else []
        report_date = datetime.now().strftime("%Y-%m-%d")

        grounding_instructions = """
YOU ARE GENERATING A FOLLOW THE MONEY REPORT.
You MUST output every section exactly in this order and never omit sections.
Analyze the supplied data. Do not summarize sources. Produce the report structure.
Use only the supplied context.
Never invent facts, statistics, dates, or market prices.
If information is unavailable, write: "Data unavailable."
Do not generate or infer a report date; use the supplied report date below.
Every major claim must reference the supplied context.
"""

        with PerformanceTimer("Prompt Construction", record_key="Prompt Construction"):
            final_prompt = f"""
REPORT DATE: {report_date}
{grounding_instructions}

=== DATA START ===
{context_text}
=== DATA END ===

REPORT FRAMEWORK:
{prompt}

SOURCES USED:
{chr(10).join(f'- {source}' for source in sources) if sources else '- Data unavailable.'}
"""
        log.info("Prompt Length: %d chars", len(final_prompt))

        use_ollama = os.getenv("USE_OLLAMA", "1").lower() in {"1", "true", "yes"}
        log.info("Using Ollama backend: %s", use_ollama)
        log.info("Ollama request start; prompt length=%d", len(final_prompt))

        if use_ollama:
            log.info("Calling Ollama generation path")
            with PerformanceTimer("Ollama Generation", record_key="Ollama Generation"):
                return ReportGenerator._generate_with_ollama(final_prompt, sources, isinstance(market_context, dict), report_date)

        if os.getenv("USE_MOCK_OPENAI", "").lower() in {"1", "true", "yes"}:
            log.info("Using mock OpenAI mode")
            return ReportGenerator._generate_mock_report(final_prompt)

        log.info("Calling OpenAI chat completion")

        try:
            content = ReportGenerator._generate_with_openai(final_prompt, sources, isinstance(market_context, dict))
        except RateLimitError as exc:
            raise RuntimeError(
                "OpenAI request failed because this API key has no "
                "available quota right now. Check your OpenAI billing, "
                "usage limits, and whether the key belongs to the "
                "intended account or project. To test the app without "
                "the API, set USE_MOCK_OPENAI=1."
            ) from exc
        except APIConnectionError as exc:
            raise RuntimeError(
                "OpenAI request failed because the API could not be reached. "
                "Check your internet connection and try again."
            ) from exc
        except APIStatusError as exc:
            raise RuntimeError(
                f"OpenAI request failed with status {exc.status_code}. "
                "Check your API key, model access, and billing details."
            ) from exc

        with PerformanceTimer("Validation", record_key="Validation"):
            is_valid = ReportGenerator._validate_report_output(content, report_date, sources)

        if not is_valid:
                log.warning(
                    "Validation failed. Returning generated report."
                )

        if isinstance(market_context, dict):
            content = ReportGenerator._append_sources_section(content, sources)
        log.info("Model request finish; response length=%d", len(content))
        return content

    @staticmethod
    def _generate_with_openai(final_prompt: str, sources: list[str], include_sources: bool):
        client = get_client()
        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are generating a FOLLOW THE MONEY report. "
                        "Analyze the supplied data. Do not summarize sources. "
                        "Output the report structure exactly in the provided framework order. "
                        "If data is unavailable, write 'Data unavailable.'"
                    )
                },
                {"role": "user", "content": final_prompt},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content or ""
        if include_sources:
            content = ReportGenerator._append_sources_section(content, sources)
        return content

    @staticmethod
    def _generate_with_ollama(final_prompt: str, sources: list[str], include_sources: bool, report_date: str):
        try:
            client, model_name = get_ollama_client()
            log.info("Starting Ollama generation with model=%s", model_name)
            request_started_at = time.perf_counter()
            response = client.generate(
                                            model=model_name,
                                            prompt=final_prompt,
                                            stream=True,
                                            options={
                                                "num_predict": int(
                                                    os.getenv(
                                                        "MAX_GENERATION_TOKENS",
                                                        "3500"
                                                    )
                                                ),
                                                "temperature": 0.2,
                                            },
                                        )
            content = ReportGenerator._collect_streamed_response(response, request_started_at)

            if not content:
                raise RuntimeError("Ollama returned an empty response.")

            with PerformanceTimer("Validation", record_key="Validation"):
                is_valid = ReportGenerator._validate_report_output(content, report_date, sources)

            if not is_valid:
                log.warning(
                    "Validation failed. Returning generated report."
                )

            if not is_valid:
                log.warning("Validation failed. Returning generated report.")

            if include_sources:
                content = ReportGenerator._append_sources_section(content, sources)
            generation_elapsed = time.perf_counter() - request_started_at
            log.info("Response Length: %d chars", len(content))

            estimated_tokens = len(content) // 4
            log.info("Estimated Tokens: %d", estimated_tokens)

            log.info("Generation Speed: %.2f chars/sec", len(content) / generation_elapsed if generation_elapsed > 0 else 0.0)
            log.info("Ollama request finish; response length=%d", len(content))
            return content
        except Exception as exc:
            raise RuntimeError(
                "Ollama request failed. Start Ollama with `ollama serve`, then run "
                "`ollama pull qwen3` (or set OLLAMA_MODEL to an installed model) "
                "before retrying."
            ) from exc

    @staticmethod
    def _collect_streamed_response(
        response: Any,
        request_started_at: float
    ) -> str:
        MAX_REPORT_CHARS = int(
            os.getenv("MAX_REPORT_CHARS", "25000")
        )

        chunks: list[str] = []
        total_chars = 0
        chunk_count = 0

        if isinstance(response, dict):
            text = response.get("response", "") or ""

            if len(text) > MAX_REPORT_CHARS:
                log.warning(
                    "Response exceeded MAX_REPORT_CHARS=%d. Truncating.",
                    MAX_REPORT_CHARS,
                )
                text = text[:MAX_REPORT_CHARS]

            return text

        try:
            first_token_logged = False

            for chunk in response:
                chunk_count += 1

                if isinstance(chunk, dict):
                    text = chunk.get("response", "") or ""
                else:
                    text = str(chunk)

                if not text:
                    continue

                if not first_token_logged:
                    first_token_logged = True
                    log.info(
                        "[PERF] Ollama first token after %.2f sec",
                        time.perf_counter() - request_started_at,
                    )

                total_chars += len(text)

                if total_chars > MAX_REPORT_CHARS:
                    remaining = (
                        MAX_REPORT_CHARS
                        - (total_chars - len(text))
                    )

                    if remaining > 0:
                        chunks.append(text[:remaining])

                    log.warning(
                        "Maximum report size reached "
                        "(MAX_REPORT_CHARS=%d). "
                        "Stopping stream collection.",
                        MAX_REPORT_CHARS,
                    )
                    break

                chunks.append(text)

            final_text = "".join(chunks)

            log.info(
                "[PERF] Stream collection complete | "
                "chunks=%d | chars=%d",
                chunk_count,
                len(final_text),
            )

            return final_text

        except TypeError:
            log.warning(
                "Unexpected Ollama response type: %s",
                type(response).__name__,
            )

            text = str(response)

            if len(text) > MAX_REPORT_CHARS:
                text = text[:MAX_REPORT_CHARS]

            return text

    @staticmethod
    def _validate_report_structure(content: str) -> bool:
        normalized = "\n".join(line.strip() for line in content.splitlines())
        return all(header in normalized for header in ReportGenerator.REQUIRED_SECTION_HEADERS)

    @staticmethod
    def _validate_report_output(content: str, report_date: str, sources: list[str]) -> bool:
        normalized = "\n".join(line.strip() for line in content.splitlines()).lower()
        has_required_sections = ReportGenerator._validate_report_structure(content)
        has_report_date = report_date in content or "date:" in normalized
        has_sources_section = "sources used:" in normalized or not sources
        return has_required_sections and has_report_date and has_sources_section

    @staticmethod
    def _append_sources_section(content: str, sources: list[str]) -> str:
        if "SOURCES USED" in content:
            return content

        citation_lines = ["SOURCES USED:"] + ([f"- {source}" for source in sources] if sources else ["- Data unavailable."])
        return f"{content.rstrip()}\n\n" + "\n".join(citation_lines)

    @staticmethod
    def _generate_mock_report(final_prompt: str):

        prompt_preview = final_prompt.strip()[:1200]

        return (
            "MOCK REPORT MODE\n\n"
            "OpenAI was bypassed because USE_MOCK_OPENAI is enabled.\n"
            "This lets you test the project wiring without consuming API quota.\n\n"
            "Prompt preview:\n"
            f"{prompt_preview}\n"
        )
