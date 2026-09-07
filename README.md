# Mobile SERP Position Checker

Flask tool for checking a domain or exact URL position in Google mobile organic results for a selected GEO.

## Run in GitHub Codespaces

```bash
pip install -r requirements.txt
export SERPAPI_KEY="YOUR_KEY"
python app.py
```

Open port `8000` from the Codespaces Ports tab.

## Important

The app uses SerpApi instead of directly scraping Google. The API key is read only from the `SERPAPI_KEY` environment variable and should never be committed to GitHub.
