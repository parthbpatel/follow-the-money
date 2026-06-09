# Follow the Money

Generate AI-assisted market reports using crypto price data, Reuters news, and report prompts for daily, weekly, and monthly updates.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add your OpenAI API key to `.env`:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

## Run

```bash
python -m src.main
```

## Prompts

Prompt templates live in `prompts/`:

- `daily.txt`
- `weekly.txt`
- `monthly.txt`
