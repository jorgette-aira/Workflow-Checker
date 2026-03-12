# Workflow-Checker Automation

## Project Structure

```
Workflow-Checker/
├── main.py            # Master Controller; manages routing, execution, and reporting
├── metrics.py         # Integration with Deepeval; contains scoring logic and metrics definitions
├── config.py          # Static configurations (Discord IDs, and User Maps)
├── requirements.txt   # Python dependencies
├── test_cases.json    # Dataset containing questions and expected answers
├── .github/           # CI/CD for Github Actions UI and automation
│   ├── workflows/
│   └── main.yml
```
## Get Started

### Prerequisites
* **N8N:** Self-hosted or cloud instance with your workflow.
* **Telegram Api:** 'API_ID' and 'API_HASH.
* **OpenAI API Key:** Required for DeepEval and LLM-assisted grading.

### Github Secrets Configurations
| Secret Name | Description |
```
| `TELEGRAM_API_ID` | Your Telegram API ID (numbers only). |
| `TELEGRAM_API_HASH` | Your Telegram API Hash string. |
| `TELEGRAM_SESSION` | Telethon String Session for headless login. |
| `N8N_WEBHOOK_URL` | The **Production** URL for your n8n workflow. |
| `OPENAI_API_KEY` | OpenAI API Key for DeepEval. |
| `TS_OAUTH_CLIENT_ID` | Tailscale OAuth Client ID. |
| `TS_OAUTH_SECRET` | Tailscale OAuth Secret. |
```

