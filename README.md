# Workflow-Checker Automation

## Project Structure

```
Workflow-Checker/
├── main.py              # Master Controller; manages routing, execution and reporting
├── metrics.py         # Integration with Deepeval; contains scoring logic and metrics definitions
├── config.py            # Static configurations (Discord IDs, and User Maps)
├── requirements.txt     # Python dependencies
├── test_cases.json      # Dataset containing questions and expected answers
├── .github/             # CI/CD for Github Actions UI and automation
│   ├── workflows/
│   └── main.yml
```
