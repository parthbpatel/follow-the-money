# Follow the Money

Follow the Money is a grounded macro-intelligence platform that generates daily, weekly, and monthly reports using live market data, Tavily web search, and local Ollama models.

## Current architecture

- Tavily search for macro and capital-flow evidence
- CoinGecko market data for crypto prices
- Context builder to combine evidence into one grounded input
- Ollama-backed report generation with source citations

## Setup

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a local `.env` file in the project root with:

```env
USE_OLLAMA=1
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:4b
TAVILY_API_KEY=your_tavily_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
USE_MOCK_OPENAI=0
```

Start Ollama locally if you are using the local model path:

```bash
ollama serve
ollama pull qwen3:4b
```

## Run

```bash
python -m src.main
```

## Notes

- Reuters RSS support has been replaced with Tavily-based macro news gathering.
- Reports are intentionally grounded in supplied context and include source references.

## Prompts

Prompt templates live in `prompts/`:

- `daily.txt`
- `weekly.txt`
- `monthly.txt`
