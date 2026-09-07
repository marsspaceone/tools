def extract_keyword(search_url: str) -> tuple[str, str]:

    search_url = (search_url or "").strip()

    if not search_url:
        return "", ""

    if "://" not in search_url:
        search_url = "https://" + search_url

    final_url = search_url

    # Если это короткая Google Share ссылка —
    # открываем её и получаем конечный URL
    if "share.google" in urlparse(search_url).netloc.lower():

        try:
            response = requests.get(
                search_url,
                allow_redirects=True,
                timeout=15,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 "
                        "(Linux; Android 14; Mobile) "
                        "AppleWebKit/537.36 "
                        "(KHTML, like Gecko) "
                        "Chrome/128.0 Mobile Safari/537.36"
                    )
                }
            )

            final_url = response.url

        except requests.RequestException:
            return "", search_url


    parsed = urlparse(final_url)

    params = parse_qs(parsed.query)


    # Обычный Google Search URL
    keyword = params.get("q", [""])[0]


    # Дополнительные варианты
    if not keyword:
        keyword = params.get("query", [""])[0]

    if not keyword:
        keyword = params.get("keyword", [""])[0]


    keyword = unquote_plus(keyword).strip()

    return keyword, final_url
