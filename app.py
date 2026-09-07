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


def normalize_domain(value):
    value = (value or "").strip().lower()

    if not value:
        return ""

    if "://" not in value:
        value = "https://" + value

    host = urlparse(value).hostname or ""

    if host.startswith("www."):
        host = host[4:]

    return host.rstrip(".")


def domain_matches(result_url, target_domain):
    result_domain = normalize_domain(result_url)

    return (
        result_domain == target_domain
        or result_domain.endswith("." + target_domain)
    )


def resolve_search_url(search_url):
    """
    Возвращает:
    keyword, final_url
    """

    search_url = (search_url or "").strip()

    if not search_url:
        return "", ""

    if "://" not in search_url:
        search_url = "https://" + search_url

    final_url = search_url

    parsed_original = urlparse(search_url)
    host = parsed_original.netloc.lower()

    # Обычная ссылка Google с ?q=
    original_params = parse_qs(parsed_original.query)

    keyword = original_params.get("q", [""])[0]

    if keyword:
        return unquote_plus(keyword).strip(), search_url


    # Короткая share.google ссылка
    if host == "share.google" or host.endswith(".share.google"):

        headers = {
            "User-Agent": (
                "Mozilla/5.0 "
                "(Linux; Android 14; Pixel 8) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/140.0 Mobile Safari/537.36"
            )
        }

        response = requests.get(
            search_url,
            headers=headers,
            allow_redirects=True,
            timeout=20
        )

        final_url = response.url


    parsed = urlparse(final_url)

    params = parse_qs(parsed.query)

    keyword = params.get("q", [""])[0]

    if not keyword:
        keyword = params.get("query", [""])[0]

    if not keyword:
        keyword = params.get("keyword", [""])[0]

    return unquote_plus(keyword).strip(), final_url


def check_position(keyword, domain, geo, api_key):

    gl, hl = GEOS[geo]

    params = {
        "engine": "google",
        "q": keyword,
        "api_key": api_key,
        "gl": gl,
        "hl": hl,
        "device": "mobile",
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

    for item in organic_results:

        position = item.get("position")

        if position is None:
            continue

        try:
            position = int(position)
        except Exception:
            continue

        if position > 30:
            continue

        result_url = item.get("link", "")

        if not result_url:
            continue

        if domain_matches(
            result_url,
            target_domain
        ):

            found_result = {
                "position": position,
                "url": result_url,
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
            }

            break

    return found_result


st.set_page_config(
    page_title="Mobile SERP Checker",
    page_icon="📱",
    layout="centered"
)


st.markdown(
    """
    <style>

    .block-container {
        max-width: 950px;
        padding-top: 40px;
    }

    h1 {
        font-size: 48px !important;
    }

    div[data-testid="stTextInput"] input {
        min-height: 58px;
        border-radius: 12px;
    }

    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        min-height: 58px;
        border-radius: 12px;
    }

    div.stButton > button {
        min-height: 58px;
        border-radius: 12px;
        font-size: 17px;
        font-weight: 700;
    }

    .result-box {
        margin-top: 25px;
        padding: 28px;
        border-radius: 18px;
        border: 1px solid #d9d9d9;
    }

    .position {
        font-size: 60px;
        font-weight: 900;
        line-height: 1;
        margin: 12px 0 20px 0;
    }

    </style>
    """,
    unsafe_allow_html=True
)


st.title("📱 Mobile SERP Checker")

st.write(
    "Проверка позиции домена по Google-ссылке в мобильной выдаче."
)


search_url = st.text_input(
    "URL поиска *",
    placeholder="https://share.google/..."
)


domain = st.text_input(
    "Домен *",
    placeholder="northcasinos.ca"
)


geo = st.selectbox(
    "GEO",
    list(GEOS.keys()),
    index=list(GEOS.keys()).index("Canada")
)


st.info(
    "Устройство: Mobile • Проверка: TOP 30"
)


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

        st.error("Введите URL поиска.")


    elif not normalize_domain(domain):

        st.error("Введите домен.")


    elif not api_key:

        st.error(
            "Не найден SERPAPI_KEY."
        )


    else:

        try:

            with st.spinner(
                "Открываю Google-ссылку..."
            ):

                keyword, final_url = resolve_search_url(
                    search_url
                )


            if not keyword:

                st.error(
                    "Ссылку удалось открыть, но поисковый запрос из неё получить не удалось."
                )

                st.write(
                    "**Конечный URL:**",
                    final_url
                )

                st.stop()


            st.success(
                f"Запрос определён: {keyword}"
            )


            with st.spinner(
                f"Проверяю Mobile / {geo}..."
            ):

                hit = check_position(
                    keyword,
                    domain,
                    geo,
                    api_key
                )


            if hit:

                st.markdown(
                    f"""
                    <div class="result-box">

                    <b>✅ ДОМЕН НАЙДЕН</b>

                    <div class="position">
                    #{hit["position"]}
                    </div>

                    <b>Запрос:</b><br>
                    {keyword}

                    <br><br>

                    <b>GEO:</b><br>
                    {geo}

                    <br><br>

                    <b>Ranking URL:</b><br>
                    {hit["url"]}

                    </div>
                    """,
                    unsafe_allow_html=True
                )


            else:

                st.error(
                    "Домен не найден в TOP 30."
                )

                st.write(
                    "**Запрос:**",
                    keyword
                )

                st.write(
                    "**Домен:**",
                    domain
                )

                st.write(
                    "**GEO:**",
                    geo
                )


        except requests.Timeout:

            st.error(
                "Google или SERP API не ответил вовремя."
            )


        except requests.RequestException as exc:

            st.error(
                f"Ошибка сети: {exc}"
            )


        except Exception as exc:

            st.error(
                f"Ошибка приложения: {exc}"
            )


st.caption(
    "Google Mobile • TOP 30"
)
