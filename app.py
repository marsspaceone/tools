import os
from urllib.parse import urlparse, urlunparse

import requests
from flask import Flask, render_template, request

app = Flask(__name__)

SERPAPI_ENDPOINT = "https://serpapi.com/search.json"

GEOS = {
    "Ghana": ("gh", "en"),
    "United Kingdom": ("gb", "en"),
    "Germany": ("de", "de"),
    "France": ("fr", "fr"),
    "Italy": ("it", "it"),
    "Spain": ("es", "es"),
    "Portugal": ("pt", "pt"),
    "Netherlands": ("nl", "nl"),
    "Belgium": ("be", "nl"),
    "Poland": ("pl", "pl"),
    "Czech Republic": ("cz", "cs"),
    "Slovakia": ("sk", "sk"),
    "Austria": ("at", "de"),
    "Switzerland": ("ch", "de"),
    "Ireland": ("ie", "en"),
    "Canada": ("ca", "en"),
    "Australia": ("au", "en"),
    "India": ("in", "en"),
    "Ukraine": ("ua", "uk"),
    "United States": ("us", "en"),
}


def normalize_domain(value: str) -> str:
    value = (value or "").strip().lower()
    if not value:
        return ""
    if "://" not in value:
        value = "https://" + value
    host = urlparse(value).hostname or ""
    if host.startswith("www."):
        host = host[4:]
    return host.rstrip(".")


def normalize_url(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if "://" not in value:
        value = "https://" + value
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = parsed.path.rstrip("/") or "/"
    return urlunparse(("https", host, path, "", "", ""))


def domain_matches(result_url: str, target_domain: str) -> bool:
    host = normalize_domain(result_url)
    return host == target_domain or host.endswith("." + target_domain)


def url_matches(result_url: str, target_url: str) -> bool:
    return normalize_url(result_url) == normalize_url(target_url)


def check_position(keyword: str, domain: str, target_url: str, geo: str, api_key: str):
    gl, hl = GEOS[geo]
    params = {
        "engine": "google",
        "q": keyword,
        "api_key": api_key,
        "gl": gl,
        "hl": hl,
        "device": "mobile",
        "num": 100,
        "filter": "0",
        "safe": "off",
    }

    response = requests.get(SERPAPI_ENDPOINT, params=params, timeout=45)
    response.raise_for_status()
    data = response.json()
    if data.get("error"):
        raise RuntimeError(data["error"])

    organic = data.get("organic_results", [])
    target_domain = normalize_domain(domain)
    strict_target = normalize_url(target_url) if target_url else ""

    domain_hit = None
    exact_url_hit = None

    for item in organic:
        result_url = item.get("link", "")
        if not result_url:
            continue
        hit = {
            "position": item.get("position"),
            "url": result_url,
            "title": item.get("title", ""),
            "snippet": item.get("snippet", ""),
        }
        if strict_target and url_matches(result_url, strict_target) and exact_url_hit is None:
            exact_url_hit = hit
        if domain_matches(result_url, target_domain) and domain_hit is None:
            domain_hit = hit

    selected = exact_url_hit if strict_target else domain_hit
    return {
        "found": selected is not None,
        "hit": selected,
        "domain_hit": domain_hit,
        "exact_url_requested": bool(strict_target),
        "checked_results": len(organic),
        "geo": geo,
    }


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    form = {"keyword": "", "domain": "", "target_url": "", "geo": "Ghana"}

    if request.method == "POST":
        form = {
            "keyword": request.form.get("keyword", "").strip(),
            "domain": request.form.get("domain", "").strip(),
            "target_url": request.form.get("target_url", "").strip(),
            "geo": request.form.get("geo", "Ghana"),
        }
        api_key = os.getenv("SERPAPI_KEY", "").strip()

        if not form["keyword"]:
            error = "Введите поисковый запрос."
        elif not normalize_domain(form["domain"]):
            error = "Введите корректный домен."
        elif form["geo"] not in GEOS:
            error = "Выберите корректное GEO."
        elif not api_key:
            error = "Не задан SERPAPI_KEY. Добавьте API-ключ в переменные окружения."
        else:
            try:
                result = check_position(form["keyword"], form["domain"], form["target_url"], form["geo"], api_key)
            except requests.RequestException as exc:
                error = f"Ошибка запроса к SERP API: {exc}"
            except Exception as exc:
                error = str(exc)

    return render_template("index.html", geos=list(GEOS.keys()), form=form, result=result, error=error)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=True)
