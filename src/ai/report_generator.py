import os

from openai import APIConnectionError, APIStatusError, RateLimitError

from src.logger import log

from src.ai.ollama_client import get_ollama_client
from src.ai.openai_client import get_client


class ReportGenerator:

    @staticmethod
    def generate(prompt: str, market_context: str | dict):
        context_text = market_context["context"] if isinstance(market_context, dict) else market_context
        sources = market_context.get("sources", []) if isinstance(market_context, dict) else []

        grounding_instructions = """
CRITICAL RULES:
- Use only the supplied context.
- Do not invent facts, dates, statistics, or market prices.
- If information is unavailable, explicitly say: "Data unavailable."
- Every major claim must reference the supplied context.
- Add a SOURCES USED section at the end of the report.
"""

        final_prompt = f"""
        {prompt}

        {grounding_instructions}

        SUPPLIED CONTEXT:
        {context_text}

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

        client = get_client()
        log.info("Calling OpenAI chat completion")

        try:
            response = client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an institutional-grade macro strategist and capital flow analyst. "
                            "Use only the supplied context. Do not invent facts, dates, statistics, or prices. "
                            "If information is unavailable, say 'Data unavailable.' Every major claim must reference the supplied context."
                        )
                    },
                    {
                        "role": "user",
                        "content": final_prompt
                    }
                ],
                temperature=0.4
            )
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

        content = response.choices[0].message.content or ""
        if isinstance(market_context, dict):
            content = ReportGenerator._append_sources_section(content, sources)
        log.info("Model request finish; response length=%d", len(content))
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
