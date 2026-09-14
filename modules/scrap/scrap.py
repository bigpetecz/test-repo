import json
import os
import re
from datetime import datetime

import cloudscraper
from bs4 import BeautifulSoup


def parse_bazos_date(date_str: str) -> str:
    """Convert Bazoš date format 'DD.M. YYYY' to ISO format 'YYYY-MM-DDTHH:MM:SS'."""
    try:
        # Extract date from format like "11.9. 2026"
        date_obj = datetime.strptime(date_str.strip(), "%d.%m. %Y")
        return date_obj.isoformat(timespec="seconds")
    except (ValueError, AttributeError):
        return "N/A"


def format_czech_date(iso_date_str: str) -> str:
    """Convert ISO datetime string to readable Czech format 'DD. M. YYYY HH:MM'."""
    if iso_date_str == "N/A":
        return "N/A"
    try:
        date_obj = datetime.fromisoformat(iso_date_str)
        # Format: "2. 9. 2026 13:56" (Czech format)
        return date_obj.strftime("%-d. %-m. %Y %H:%M")
    except (ValueError, AttributeError):
        return "N/A"

RESULTS_FILE = "search_results.json"

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


def load_previous_results(path: str = RESULTS_FILE) -> dict:
    """Load the accumulated listing history, keyed by link (url is the unique key)."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def save_results(history: dict, current_items: list, path: str = RESULTS_FILE) -> None:
    """Merge current results into the stored history additively - every ad ever seen is kept
    forever (flagged "active"/"removed") so past ads stay trackable even after they vanish."""
    now = datetime.now().isoformat(timespec="seconds")
    current_links = {item["link"] for item in current_items}

    # Anything still active but missing from this run just went away - flag it, don't delete it.
    for link, entry in history.items():
        if link not in current_links and entry.get("status") != "removed":
            entry["status"] = "removed"
            entry["removed_at"] = now

    for item in current_items:
        entry = history.get(item["link"], {})
        entry.update(item)
        entry["first_seen"] = entry.get("first_seen", now)
        entry["last_seen"] = now
        entry["status"] = "active"
        entry.pop("removed_at", None)
        history[item["link"]] = entry

    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def passes_filter(text: str) -> bool:
    """
    Flexible matching for 64GB RAM and M1/M2/M3 Max chips.
    Matches variations like '64GB', '64 GB', 'M1 Max', 'M2MAX', etc.
    """
    text_lower = text.lower()

    # Matches "64gb", "64 gb", "64-gb", "64g"
    has_64gb = bool(re.search(r"\b64\s*-?\s*gb?\b", text_lower))

    # Matches "m1 max", "m2 max", "m3 max" (with optional spaces/hyphens)
    has_max_chip = bool(re.search(r"\bm[1-3]\s*-?\s*max\b", text_lower))

    return has_64gb and has_max_chip


def search_bazos(max_pages: int = 2):
    print("--- Searching Bazoš.cz ---")
    found_items = []
    scraper = cloudscraper.create_scraper()

    for page in range(max_pages):
        # Bazoš pagination uses offset by 20 (0, 20, 40...), placed at the root path
        # (e.g. https://pc.bazos.cz/20/?hledat=...), not nested under a category slug.
        # "hledat=64GB" alone matches ~360 generic PC listings; narrowing the search
        # term itself to "macbook 64gb" brings the relevant result set down to ~17,
        # so it fits on a single page and pagination isn't even required to see them all.
        start_offset = page * 20
        url = (
            f"https://pc.bazos.cz/{start_offset}/?hledat=macbook+64gb&rubriky=pc"
            if start_offset > 0
            else "https://pc.bazos.cz/?hledat=macbook+64gb&rubriky=pc"
        )

        try:
            response = scraper.get(url, timeout=10)
            if response.status_code == 404:
                # Bazoš returns 404 once you request a page past the last one, not a real error.
                break
            if response.status_code != 200:
                print(f"Failed to fetch Bazoš (page {page + 1}). Status code: {response.status_code}")
                break

            soup = BeautifulSoup(response.text, "html.parser")
            listings = soup.find_all("div", class_="inzeraty") + soup.find_all("table", class_="inzeraty")

            if not listings:
                break

            for item in listings:
                title_tag = item.find(["h2", "span"], class_="nadpis")
                desc_tag = item.find("div", class_="popis")
                price_tag = item.find("div", class_="inzeratycena")
                loc_tag = item.find("div", class_="inzeratylok")

                if title_tag and title_tag.find("a"):
                    a_tag = title_tag.find("a")
                    href = a_tag["href"]
                    link = href if href.startswith("http") else f"https://pc.bazos.cz{href}"

                    # Bazoš sometimes serves an alternate template where the link text is
                    # server-side truncated (e.g. "...RA ..."); the image alt attribute
                    # always carries the untruncated title, so prefer that when present.
                    img_tag = item.find("img", alt=True)
                    title = img_tag["alt"].strip() if img_tag else a_tag.text.strip()

                    description = desc_tag.text.strip() if desc_tag else ""
                    price = price_tag.get_text(strip=True) if price_tag else "N/A"
                    # Location is city and ZIP separated by a <br>, e.g. "Praha 5<br>155 21".
                    location = loc_tag.get_text(", ", strip=True) if loc_tag else "N/A"

                    if desc_tag and (price == "N/A" or location == "N/A"):
                        # That same alternate template folds price/location into the tail of
                        # div.popis instead of separate inzeratycena/inzeratylok divs.
                        lines = [ln.strip() for ln in desc_tag.get_text("\n").split("\n") if ln.strip()]
                        if price == "N/A" and lines and re.search(r"K[cč]\s*$", lines[-1], re.IGNORECASE):
                            price = lines.pop()
                        if location == "N/A" and lines and re.match(r"^.+ - \d", lines[-1]):
                            location = lines.pop().replace(" - ", ", ")
                        if lines:
                            description = "\n".join(lines).strip()

                    full_text = f"{title} {description}"

                    # Extract posting date from span.velikost10 containing "[DD.M. YYYY]"
                    posted_date = "N/A"
                    detail_span = item.find("span", class_="velikost10")
                    if detail_span:
                        detail_text = detail_span.get_text()
                        # Extract date from format like " - [11.9. 2026]"
                        date_match = re.search(r"\[(\d{1,2}\.\d{1,2}\. \d{4})\]", detail_text)
                        if date_match:
                            posted_date = parse_bazos_date(date_match.group(1))

                    if passes_filter(full_text):
                        found_items.append({
                            "platform": "Bazoš",
                            "title": title,
                            "price": price,
                            "location": location,
                            "link": link,
                            "posted_date": posted_date,
                        })

        except Exception as e:
            print(f"Error scraping Bazoš page {page + 1}: {e}")
            break

    return found_items


def search_sbazar(max_pages: int = 3):
    # Sbazar retired its public JSON search API (now returns 404/401), so this scrapes
    # the server-rendered search page HTML instead. Pagination uses page numbers, not offsets.
    print("--- Searching Sbazar.cz ---")
    # Searching "macbook-pro" alone returns generic listings whose titles rarely mention
    # RAM/chip specs, so passes_filter (title-only) almost never matches. Narrowing the
    # query itself to include "64gb" makes Sbazar's own search surface the relevant ads.
    query_slug = "macbook-pro-64gb"
    base_url = f"https://www.sbazar.cz/hledej/{query_slug}"

    scraper = cloudscraper.create_scraper()
    found_items = []
    seen_links = set()

    for page in range(1, max_pages + 1):
        url = (
            base_url
            if page == 1
            else f"{base_url}/0-vsechny-kategorie/cela-cr/cena-neomezena/nejnovejsi/{page}"
        )

        try:
            response = scraper.get(url, timeout=10)
            if response.status_code == 404:
                # No more result pages for this query.
                break
            if response.status_code != 200:
                print(f"Failed to fetch Sbazar (page {page}). Status code: {response.status_code}")
                break

            soup = BeautifulSoup(response.text, "html.parser")
            cards = [a for a in soup.find_all("a", href=True) if a["href"].startswith("/inzerat/")]

            if not cards:
                break

            for a_tag in cards:
                link = f"https://www.sbazar.cz{a_tag['href']}"
                if link in seen_links:
                    continue
                seen_links.add(link)

                title_tag = a_tag.find("div", class_="line-clamp-2")
                info_tag = a_tag.find("div", class_="line-clamp-1")

                title = title_tag.get_text(strip=True) if title_tag else ""
                price = info_tag.find("b").get_text(strip=True) if info_tag and info_tag.find("b") else "N/A"
                location = info_tag.find("span").get_text(strip=True) if info_tag and info_tag.find("span") else "N/A"

                # Extract posting date from <time datetime="..."> element
                # The time element is in a sibling div, so search in the parent
                posted_date = "N/A"
                parent = a_tag.parent
                if parent:
                    time_tag = parent.find("time")
                    if time_tag and time_tag.get("datetime"):
                        posted_date = time_tag["datetime"]

                # Listing cards don't expose the description, so filtering only sees the title.
                if passes_filter(title):
                    found_items.append({
                        "platform": "Sbazar",
                        "title": title,
                        "price": price,
                        "location": location,
                        "link": link,
                        "posted_date": posted_date,
                    })

        except Exception as e:
            print(f"Error scraping Sbazar page {page}: {e}")
            break

    return found_items


if __name__ == "__main__":
    bazos_results = search_bazos(max_pages=2)
    sbazar_results = search_sbazar(max_pages=3)

    all_results = bazos_results + sbazar_results
    current_links = {item["link"] for item in all_results}

    previous_results = load_previous_results()
    new_links = current_links - previous_results.keys()
    # Only ads that were still "active" last run and are now gone count as newly disappeared;
    # ones already flagged "removed" before stay in the file forever but aren't re-reported.
    disappeared_links = {
        link for link, entry in previous_results.items()
        if link not in current_links and entry.get("status") != "removed"
    }

    print(f"\nFound {len(all_results)} matching listing(s):\n" + "=" * 40)
    if not all_results:
        print("No matching listings found right now.")
    else:
        for idx, item in enumerate(all_results, 1):
            is_new = item["link"] in new_links
            color = GREEN if is_new else ""
            reset = RESET if is_new else ""
            tag = " [NEW]" if is_new else ""
            
            # Get dates from history if available
            history_entry = previous_results.get(item["link"], {})
            first_seen = format_czech_date(history_entry.get("first_seen", "N/A"))
            last_seen = format_czech_date(history_entry.get("last_seen", "N/A"))
            
            print(f"{color}{idx}. [{item['platform']}] {item['title']}{tag}{reset}")
            print(f"{color}   Price:      {item['price']}{reset}")
            print(f"{color}   Location:   {item['location']}{reset}")
            posted_date = format_czech_date(item.get("posted_date", "N/A"))
            print(f"{color}   Posted:     {posted_date}{reset}")
            print(f"{color}   First seen: {first_seen}{reset}")
            print(f"{color}   Last seen:  {last_seen}{reset}")
            print(f"{color}   Link:       {item['link']}{reset}")
            print("-" * 40)

    if disappeared_links:
        print(f"\n{RED}Disappeared since last search ({len(disappeared_links)}):{RESET}\n" + "=" * 40)
        for link in disappeared_links:
            item = previous_results[link]
            removed_at = format_czech_date(item.get("removed_at", "N/A"))
            first_seen = format_czech_date(item.get("first_seen", "N/A"))
            last_seen = format_czech_date(item.get("last_seen", "N/A"))
            posted_date = format_czech_date(item.get("posted_date", "N/A"))
            print(f"{RED}- [{item['platform']}] {item['title']} [GONE]{RESET}")
            print(f"{RED}   Price:      {item['price']}{RESET}")
            print(f"{RED}   Location:   {item['location']}{RESET}")
            print(f"{RED}   Posted:     {posted_date}{RESET}")
            print(f"{RED}   First seen: {first_seen}{RESET}")
            print(f"{RED}   Last seen:  {last_seen}{RESET}")
            print(f"{RED}   Removed at: {removed_at}{RESET}")
            print(f"{RED}   Link:       {item['link']}{RESET}")
            print("-" * 40)

    save_results(previous_results, all_results)