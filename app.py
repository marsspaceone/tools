import os
from urllib.parse import urlparse, urlunparse

import requests
import streamlit as st

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

    return urlunparse(
        (
            "https",
            host,
            path,
            "",
            "",
            "",
        )
    )


def domain_matches(result_url: str, target_domain: str) -> bool:
    host = normalize_domain(result_url)

    return (
        host == target_domain
        or host.endswith("." + target_domain)
    )


def url_matches(result_url: str, target_url: str) -> bool:
    return normalize_url(result_url) == normalize_url(target_url)


def check_position(
    keyword: str,
    domain: str,
    target_url: str,
    geo: str,
    api_key: str,
):

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

    response = requests.get(
        SERPAPI_ENDPOINT,
        params=params,
        timeout=45,
    )

    response.raise_for_status()

    data = response.json()

    if data.get("error"):
        raise RuntimeError(data["error"])

    organic = data.get("organic_results", [])

    target_domain = normalize_domain(domain)

    strict_target = (
        normalize_url(target_url)
        if target_url
        else ""
    )

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

        if (
            strict_target
            and url_matches(result_url, strict_target)
            and exact_url_hit is None
        ):
            exact_url_hit = hit

        if (
            domain_matches(result_url, target_domain)
            and domain_hit is None
        ):
            domain_hit = hit

    selected = (
        exact_url_hit
        if strict_target
        else domain_hit
    )

    return {
        "found": selected is not None,
        "hit": selected,
        "domain_hit": domain_hit,
        "exact_url_requested": bool(strict_target),
        "checked_results": len(organic),
        "geo": geo,
    }


st.set_page_config(
    page_title="Mobile SERP Position Checker",
    page_icon="📱",
    layout="centered",
)


st.markdown(
    """
    <style>

    .block-container {
        max-width: 900px;
        padding-top: 40px;
        padding-bottom: 60px;
    }

    .main-title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .subtitle {
        font-size: 16px;
        color: #888;
        margin-bottom: 30px;
    }

    .result-box {
        padding: 25px;
        border-radius: 16px;
        border: 1px solid #2d2d2d;
        margin-top: 20px;
    }

    .position {
        font-size: 48px;
        font-weight: 800;
        margin: 10px 0;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    '<div class="main-title">📱 Mobile SERP Checker</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="subtitle">
    Проверка позиции домена в мобильной выдаче Google по выбранному GEO.
    </div>
    """,
    unsafe_allow_html=True,
)


keyword = st.text_input(
    "Поисковый запрос",
    placeholder="например: chicken road casino",
)


domain = st.text_input(
    "Домен",
    placeholder="например: chickenroad-app-bonus.net",
)


target_url = st.text_input(
    "Конкретный URL — необязательно",
    placeholder="https://example.com/page/",
)


geo = st.selectbox(
    "GEO",
    list(GEOS.keys()),
)


st.info(
    "Устройство: Mobile • Глубина проверки: до TOP 100"
)


if st.button(
    "Проверить позицию",
    use_container_width=True,
):

    api_key = ""

    try:
        api_key = st.secrets["SERPAPI_KEY"]
    except Exception:
        api_key = os.getenv(
            "SERPAPI_KEY",
            "",
        )

    if not keyword:
        st.error("Введите поисковый запрос.")

    elif not normalize_domain(domain):
        st.error("Введите корректный домен.")

    elif not api_key:
        st.error(
            "Не найден SERPAPI_KEY. Добавьте ключ в Streamlit Secrets."
        )

    else:

        with st.spinner(
            "Проверяю мобильную выдачу Google..."
        ):

            try:

                result = check_position(
                    keyword,
                    domain,
                    target_url,
                    geo,
                    api_key,
                )

                if result["found"]:

                    hit = result["hit"]

                    st.success(
                        "Домен найден в выдаче"
                    )

                    st.markdown(
                        f"""
                        <div class="result-box">

                        <div>Позиция</div>

                        <div class="position">
                        #{hit["position"]}
                        </div>

                        <b>Ranking URL</b><br>
                        {hit["url"]}

                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if hit.get("title"):
                        st.write(
                            "**Title:**",
                            hit["title"],
                        )

                    if hit.get("snippet"):
                        st.write(
                            "**Snippet:**",
                            hit["snippet"],
                        )

                else:

                    st.error(
                        "Не найдено в TOP 100"
                    )

                    if (
                        result["exact_url_requested"]
                        and result["domain_hit"]
                    ):

                        domain_hit = result[
                            "domain_hit"
                        ]

                        st.warning(
                            "Указанный URL не найден, но другой URL этого домена ранжируется."
                        )

                        st.write(
                            "Позиция домена:",
                            f'#{domain_hit["position"]}',
                        )

                        st.write(
                            "URL:",
                            domain_hit["url"],
                        )

            except Exception as exc:

                st.error(
                    f"Ошибка: {exc}"
                )


st.caption(
    "Google Mobile • SERP API • TOP 100"
)
