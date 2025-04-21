import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote
import re
import os

OC = os.getenv("OC", "chetera")
BASE = "http://www.law.go.kr"

def get_law_list_from_api(query):
    encoded_query = quote(f'"{query}"')
    page = 1
    laws = []
    while True:
        url = f"{BASE}/DRF/lawSearch.do?OC={OC}&target=law&type=XML&display=100&page={page}&search=2&knd=A0002&query={encoded_query}"
        res = requests.get(url, timeout=10)
        res.encoding = 'utf-8'
        if res.status_code != 200:
            break
        root = ET.fromstring(res.content)
        for law in root.findall("law"):
            laws.append({
                "법령명": law.findtext("법령명한글", "").strip(),
                "MST": law.findtext("법령일련번호", "")
            })
        if len(root.findall("law")) < 100:
            break
        page += 1
    return laws

def get_law_text_by_mst(mst):
    url = f"{BASE}/DRF/lawService.do?OC={OC}&target=law&MST={mst}&type=XML"
    try:
        res = requests.get(url, timeout=10)
        res.encoding = 'utf-8'
        return res.content if res.status_code == 200 else None
    except:
        return None

def clean(text):
    return re.sub(r"\s+", "", text or "")

def highlight(text, keyword):
    if not text:
        return ""
    return text.replace(keyword, f"<span style='color:red'>{keyword}</span>")

def run_search_logic(query, unit):
    result_dict = {}
    for law in get_law_list_from_api(query):
        mst = law["MST"]
        xml = get_law_text_by_mst(mst)
        if not xml:
            continue
        tree = ET.fromstring(xml)
        articles = tree.findall(".//조문단위")
        result_html = []

        for article in articles:
            조번호 = article.findtext("조번호", "").strip()
            조제목 = article.findtext("조문제목", "") or ""
            조내용 = article.findtext("조문내용", "") or ""
            항들 = article.findall("항")

            lines = []
            if query in 조제목 or query in 조내용:
                lines.append(f"제{조번호}조({조제목}) {highlight(조내용, query)}")

            for 항 in 항들:
                항번호 = 항.findtext("항번호", "")
                항내용 = 항.findtext("항내용", "") or ""
                if query in 항내용:
                    lines.append(f"&nbsp;&nbsp;{highlight(항내용, query)}")

            if lines:
                result_html.append("<br>".join(lines))

        if result_html:
            result_dict[law["법령명"]] = result_html

    return result_dict

def extract_locations(xml_data, keyword):
    tree = ET.fromstring(xml_data)
    articles = tree.findall(".//조문단위")
    keyword_clean = clean(keyword)
    locations = []
    for article in articles:
        조번호 = article.findtext("조번호", "").strip()
        조제목 = article.findtext("조문제목", "") or ""
        조내용 = article.findtext("조문내용", "") or ""
        항들 = article.findall("항")

        if keyword_clean in clean(조제목):
            locations.append(f"제{조번호}조의 제목")
        if keyword_clean in clean(조내용):
            locations.append(f"제{조번호}조")

        for 항 in 항들:
            항번호 = 항.findtext("항번호", "").strip()
            항내용 = 항.findtext("항내용", "") or ""
            if keyword_clean in clean(항내용):
                locations.append(f"제{조번호}조제{항번호}항")
    return locations

def deduplicate(seq):
    seen = set()
    return [x for x in seq if not (x in seen or seen.add(x))]

def format_location_list(locations):
    if not locations:
        return ""
    return " 및 ".join(locations)

def get_josa(word, josa_with_batchim, josa_without_batchim):
    if not word:
        return josa_with_batchim
    last_char = word[-1]
    code = ord(last_char)
    return josa_with_batchim if (code - 44032) % 28 != 0 else josa_without_batchim

def run_amendment_logic(find_word, replace_word):
    조사 = get_josa(find_word, "을", "를")
    amendment_results = []
    for law in get_law_list_from_api(find_word):
        law_name = law["법령명"]
        mst = law["MST"]
        xml = get_law_text_by_mst(mst)
        if not xml:
            continue
        locations = extract_locations(xml, find_word)
        if not locations:
            continue
        loc_str = format_location_list(deduplicate(locations))
        sentence = f"① {law_name} 일부를 다음과 같이 개정한다. {loc_str} 중 “{find_word}”{조사} 각각 “{replace_word}”로 한다."
        amendment_results.append(sentence)
    return amendment_results if amendment_results else ["⚠️ 개정 대상 조문이 없습니다."]