from openai import APIConnectionError, APIStatusError, RateLimitError

from src.ai.openai_client import get_client


class ReportGenerator:

    @staticmethod
    def generate(prompt: str, market_context: str):

        client = get_client()

        final_prompt = f"""
        {prompt}

        MARKET CONTEXT:
        {market_context}
        """

        try:
            response = client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an institutional-grade "
                            "macro strategist and capital flow analyst."
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
                "intended account or project."
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

        return response.choices[0].message.content
