import os
from urllib.parse import urlparse, parse_qs, unquote_plus

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


# -----------------------------
# DOMAIN
# -----------------------------

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


def domain_matches(result_url: str, target_domain: str) -> bool:

    result_domain = normalize_domain(result_url)

    return (
        result_domain == target_domain
        or result_domain.endswith("." + target_domain)
    )


# -----------------------------
# SEARCH URL
# -----------------------------

def extract_keyword(search_url: str) -> str:

    search_url = (search_url or "").strip()

    if not search_url:
        return ""

    # Если человек вставил URL без https://
    if "://" not in search_url:
        search_url = "https://" + search_url

    parsed = urlparse(search_url)

    params = parse_qs(parsed.query)

    # Основной параметр Google
    keyword = params.get("q", [""])[0]

    # На случай других вариантов URL
    if not keyword:
        keyword = params.get("query", [""])[0]

    if not keyword:
        keyword = params.get("keyword", [""])[0]

    return unquote_plus(keyword).strip()


# -----------------------------
# SERP CHECK
# -----------------------------

def check_position(
    keyword: str,
    domain: str,
    geo: str,
    api_key: str
):

    gl, hl = GEOS[geo]

    params = {
        "engine": "google",
        "q": keyword,
        "api_key": api_key,

        # GEO
        "gl": gl,
        "hl": hl,

        # Главное — мобильная выдача
        "device": "mobile",

        # Берём результаты с запасом,
        # но сами анализируем только TOP 30
        "num": 30,

        "filter": "0",
        "safe": "off",
    }

    response = requests.get(
        SERPAPI_ENDPOINT,
        params=params,
        timeout=45
    )

    response.raise_for_status()

    data = response.json()

    if data.get("error"):
        raise RuntimeError(data["error"])

    organic_results = data.get(
        "organic_results",
        []
    )

    target_domain = normalize_domain(domain)

    found_result = None

    checked_results = []

    for item in organic_results:

        position = item.get("position")

        # Нас интересует исключительно TOP 30
        if not position:
            continue

        if position > 30:
            continue

        result_url = item.get("link", "")

        if not result_url:
            continue

        result_data = {
            "position": position,
            "url": result_url,
            "title": item.get("title", ""),
            "snippet": item.get("snippet", ""),
        }

        checked_results.append(result_data)

        if domain_matches(
            result_url,
            target_domain
        ):

            if found_result is None:
                found_result = result_data

    return {
        "found": found_result is not None,
        "hit": found_result,
        "checked_results": checked_results,
        "geo": geo,
        "keyword": keyword,
    }


# -----------------------------
# STREAMLIT
# -----------------------------

st.set_page_config(
    page_title="Mobile SERP Checker",
    page_icon="📱",
    layout="centered"
)


# -----------------------------
# DESIGN
# -----------------------------

st.markdown(
    """
    <style>

    .block-container {
        max-width: 950px;
        padding-top: 45px;
        padding-bottom: 60px;
    }

    .main-title {
        font-size: 48px;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 12px;
    }

    .subtitle {
        font-size: 17px;
        color: #888;
        margin-bottom: 35px;
    }

    .search-info {
        background: #eef5ff;
        border: 1px solid #d7e6ff;
        padding: 18px 20px;
        border-radius: 14px;
        margin-top: 15px;
        margin-bottom: 20px;
    }

    .result-success {
        background: #eefbf3;
        border: 1px solid #b9eccd;
        border-radius: 18px;
        padding: 28px;
        margin-top: 25px;
    }

    .result-error {
        background: #fff3f3;
        border: 1px solid #ffcaca;
        border-radius: 18px;
        padding: 28px;
        margin-top: 25px;
    }

    .position-number {
        font-size: 60px;
        font-weight: 900;
        line-height: 1;
        margin-top: 10px;
        margin-bottom: 15px;
    }

    .found-label {
        font-size: 15px;
        font-weight: 700;
    }

    div[data-testid="stTextInput"] input {
        min-height: 58px;
        border-radius: 13px;
    }

    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        min-height: 58px;
        border-radius: 13px;
    }

    div.stButton > button {
        min-height: 58px;
        border-radius: 13px;
        font-size: 17px;
        font-weight: 700;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# -----------------------------
# HEADER
# -----------------------------

st.markdown(
    """
    <div class="main-title">
        📱 Mobile SERP Checker
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="subtitle">
        Проверка позиции домена в мобильной выдаче Google
        по URL поискового запроса и выбранному GEO.
    </div>
    """,
    unsafe_allow_html=True
)


# -----------------------------
# FORM
# -----------------------------

search_url = st.text_input(
    "URL поиска *",
    placeholder="https://www.google.com/search?q=chicken+road+casino"
)


domain = st.text_input(
    "Домен *",
    placeholder="chickenroad-app-bonus.net"
)


geo = st.selectbox(
    "GEO",
    list(GEOS.keys())
)


keyword = extract_keyword(search_url)


if search_url and keyword:

    st.markdown(
        f"""
        <div class="search-info">
            <b>Запрос из URL:</b><br>
            {keyword}
            <br><br>
            📱 Mobile &nbsp;•&nbsp;
            🌍 {geo} &nbsp;•&nbsp;
            🔎 TOP 30
        </div>
        """,
        unsafe_allow_html=True
    )


elif search_url:

    st.warning(
        "В URL не найден поисковый запрос. "
        "Ожидается ссылка с параметром ?q=..."
    )


# -----------------------------
# BUTTON
# -----------------------------

if st.button(
    "Проверить позицию",
    use_container_width=True
):

    try:
        api_key = st.secrets["SERPAPI_KEY"]

    except Exception:

        api_key = os.getenv(
            "SERPAPI_KEY",
            ""
        )


    if not search_url:

        st.error(
            "Введите URL поискового запроса."
        )


    elif not keyword:

        st.error(
            "Не удалось определить запрос из URL. "
            "Пример: https://google.com/search?q=chicken+road"
        )


    elif not normalize_domain(domain):

        st.error(
            "Введите домен."
        )


    elif not api_key:

        st.error(
            "Не найден SERPAPI_KEY."
        )


    else:

        with st.spinner(
            f'Проверяю "{keyword}" — Mobile / {geo}...'
        ):

            try:

                result = check_position(
                    keyword=keyword,
                    domain=domain,
                    geo=geo,
                    api_key=api_key
                )


                # -----------------------------
                # FOUND
                # -----------------------------

                if result["found"]:

                    hit = result["hit"]

                    position = hit["position"]

                    st.markdown(
                        f"""
                        <div class="result-success">

                            <div class="found-label">
                                ✅ ДОМЕН НАЙДЕН
                            </div>

                            <div class="position-number">
                                #{position}
                            </div>

                            <div>
                                <b>Запрос:</b>
                                {keyword}
                            </div>

                            <br>

                            <div>
                                <b>GEO:</b>
                                {geo}
                            </div>

                            <br>

                            <div>
                                <b>Device:</b>
                                Mobile
                            </div>

                            <br>

                            <div>
                                <b>Ranking URL:</b><br>
                                {hit["url"]}
                            </div>

                        </div>
                        """,
                        unsafe_allow_html=True
                    )


                    if hit.get("title"):

                        st.write(
                            "**Title:**",
                            hit["title"]
                        )


                    if hit.get("snippet"):

                        st.write(
                            "**Snippet:**",
                            hit["snippet"]
                        )


                # -----------------------------
                # NOT FOUND
                # -----------------------------

                else:

                    st.markdown(
                        f"""
                        <div class="result-error">

                            <div class="found-label">
                                ❌ ДОМЕН НЕ НАЙДЕН
                            </div>

                            <br>

                            <div style="
                                font-size:30px;
                                font-weight:800;
                            ">
                                Нет в TOP 30
                            </div>

                            <br>

                            <b>Домен:</b>
                            {domain}

                            <br><br>

                            <b>Запрос:</b>
                            {keyword}

                            <br><br>

                            <b>GEO:</b>
                            {geo}

                            <br><br>

                            <b>Device:</b>
                            Mobile

                        </div>
                        """,
                        unsafe_allow_html=True
                    )


            except requests.Timeout:

                st.error(
                    "Сервис проверки не ответил вовремя."
                )


            except requests.RequestException as exc:

                st.error(
                    f"Ошибка SERP API: {exc}"
                )


            except Exception as exc:

                st.error(
                    f"Ошибка: {exc}"
                )


st.caption(
    "Google Mobile • TOP 30"
)
