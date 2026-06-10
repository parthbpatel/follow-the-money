import os

from openai import APIConnectionError, APIStatusError, RateLimitError

from src.logger import log

from src.ai.ollama_client import get_ollama_client
from src.ai.openai_client import get_client


class ReportGenerator:

    REQUIRED_SECTION_HEADERS = (
        "1. GLOBAL CAPITAL FLOW SNAPSHOT",
        "16. CORE INSIGHT",
    )

    @staticmethod
    def generate(prompt: str, market_context: str | dict):
        context_text = market_context["context"] if isinstance(market_context, dict) else market_context
        sources = market_context.get("sources", []) if isinstance(market_context, dict) else []

        grounding_instructions = """
YOU ARE GENERATING A FOLLOW THE MONEY REPORT.
You MUST output every section exactly in this order and never omit sections.
Analyze the supplied data. Do not summarize sources. Produce the report structure.
Use only the supplied context.
Do not invent facts, dates, statistics, or market prices.
If information is unavailable, write: "Data unavailable."
Every major claim must reference the supplied context.
"""

        final_prompt = f"""
{grounding_instructions}

=== DATA START ===
{context_text}
=== DATA END ===

REPORT FRAMEWORK:
{prompt}

SOURCES USED:
{chr(10).join(f'- {source}' for source in sources) if sources else '- Data unavailable.'}
"""

        use_ollama = os.getenv("USE_OLLAMA", "1").lower() in {"1", "true", "yes"}
        log.info("Using Ollama backend: %s", use_ollama)
        log.info("Ollama request start; prompt length=%d", len(final_prompt))

        if use_ollama:
            log.info("Calling Ollama generation path")
            return ReportGenerator._generate_with_ollama(final_prompt, sources, isinstance(market_context, dict))

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

        if not ReportGenerator._validate_report_structure(content):
            log.warning("Generated output missed required framework headers; retrying once.")
            content = ReportGenerator._generate_with_openai(final_prompt + "\n\nRETRY: You must output the required framework sections exactly in order.", sources, isinstance(market_context, dict))
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
    def _generate_with_ollama(final_prompt: str, sources: list[str], include_sources: bool):
        try:
            client, model_name = get_ollama_client()
            log.info("Starting Ollama generation with model=%s", model_name)
            response = client.generate(model=model_name, prompt=final_prompt, stream=False)
            content = response.get("response") if isinstance(response, dict) else getattr(response, "response", None)

            if not content:
                raise RuntimeError("Ollama returned an empty response.")

            if not ReportGenerator._validate_report_structure(content):
                log.warning("Ollama output missed required framework headers; retrying once.")
                retry_prompt = final_prompt + "\n\nRETRY: You must output the required framework sections exactly in order."
                response = client.generate(model=model_name, prompt=retry_prompt, stream=False)
                content = response.get("response") if isinstance(response, dict) else getattr(response, "response", None)

            if include_sources:
                content = ReportGenerator._append_sources_section(content, sources)
            log.info("Ollama request finish; response length=%d", len(content))
            return content
        except Exception as exc:
            raise RuntimeError(
                "Ollama request failed. Start Ollama with `ollama serve`, then run "
                "`ollama pull qwen3` (or set OLLAMA_MODEL to an installed model) "
                "before retrying."
            ) from exc

    @staticmethod
    def _validate_report_structure(content: str) -> bool:
        normalized = "\n".join(line.strip() for line in content.splitlines())
        return all(header in normalized for header in ReportGenerator.REQUIRED_SECTION_HEADERS)

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
