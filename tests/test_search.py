import unittest
from unittest.mock import Mock, patch

from modules.scrap import scrap


class SearchSmokeTests(unittest.TestCase):
    def test_search_bazos_parses_matching_listings(self):
        response = Mock(
            status_code=200,
            text="""
                <div class="inzeraty">
                    <h2 class="nadpis">
                        <a href="/inzerat/123">MacBook Pro M1 Max 64GB</a>
                    </h2>
                    <div class="popis">MacBook with 64 GB RAM and M1 Max chip</div>
                    <div class="inzeratycena">45 000 Kč</div>
                    <div class="inzeratylok">Praha<br>110 00</div>
                    <span class="velikost10"> - [11.9. 2026]</span>
                </div>
                <div class="inzeraty">
                    <h2 class="nadpis">
                        <a href="/inzerat/124">MacBook Pro M1 32GB</a>
                    </h2>
                    <div class="popis">MacBook with 32 GB RAM</div>
                </div>
            """,
        )
        scraper = Mock()
        scraper.get.return_value = response

        with patch(
            "modules.scrap.scrap.cloudscraper.create_scraper",
            return_value=scraper,
        ):
            results = scrap.search_bazos(max_pages=1)

        scraper.get.assert_called_once_with(
            "https://pc.bazos.cz/?hledat=macbook+64gb&rubriky=pc",
            timeout=10,
        )
        self.assertEqual(
            results,
            [
                {
                    "platform": "Bazoš",
                    "title": "MacBook Pro M1 Max 64GB",
                    "price": "45 000 Kč",
                    "location": "Praha, 110 00",
                    "link": "https://pc.bazos.cz/inzerat/123",
                    "posted_date": "2026-09-11T00:00:00",
                }
            ],
        )

    def test_search_sbazar_parses_matching_listings(self):
        response = Mock(
            status_code=200,
            text="""
                <div class="card">
                    <a href="/inzerat/456">
                        <div class="line-clamp-2">MacBook Pro M2 Max 64GB</div>
                        <div class="line-clamp-1">
                            <b>50 000 Kč</b><span>Brno</span>
                        </div>
                    </a>
                    <time datetime="2026-09-11T12:34:00"></time>
                </div>
                <div class="card">
                    <a href="/inzerat/457">
                        <div class="line-clamp-2">MacBook Pro M3 32GB</div>
                        <div class="line-clamp-1">
                            <b>40 000 Kč</b><span>Praha</span>
                        </div>
                    </a>
                </div>
            """,
        )
        scraper = Mock()
        scraper.get.return_value = response

        with patch(
            "modules.scrap.scrap.cloudscraper.create_scraper",
            return_value=scraper,
        ):
            results = scrap.search_sbazar(max_pages=1)

        scraper.get.assert_called_once_with(
            "https://www.sbazar.cz/hledej/macbook-pro-64gb",
            timeout=10,
        )
        self.assertEqual(
            results,
            [
                {
                    "platform": "Sbazar",
                    "title": "MacBook Pro M2 Max 64GB",
                    "price": "50 000 Kč",
                    "location": "Brno",
                    "link": "https://www.sbazar.cz/inzerat/456",
                    "posted_date": "2026-09-11T12:34:00",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
