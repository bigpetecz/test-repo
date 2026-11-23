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
                    "price_band": "premium",
                }
            ],
        )

    def test_search_bazos_price_band_classification(self):
        response = Mock(
            status_code=200,
            text="""
                <div class="inzeraty">
                    <h2 class="nadpis">
                        <a href="/inzerat/201">MacBook Pro M1 Max 64GB Budget</a>
                    </h2>
                    <div class="popis">MacBook with 64 GB RAM and M1 Max chip</div>
                    <div class="inzeratycena">19 999 Kč</div>
                    <div class="inzeratylok">Praha<br>110 00</div>
                    <span class="velikost10"> - [11.9. 2026]</span>
                </div>
                <div class="inzeraty">
                    <h2 class="nadpis">
                        <a href="/inzerat/202">MacBook Pro M1 Max 64GB Mid Lower</a>
                    </h2>
                    <div class="popis">MacBook with 64 GB RAM and M1 Max chip</div>
                    <div class="inzeratycena">20 000 Kč</div>
                    <div class="inzeratylok">Praha<br>110 00</div>
                    <span class="velikost10"> - [11.9. 2026]</span>
                </div>
                <div class="inzeraty">
                    <h2 class="nadpis">
                        <a href="/inzerat/203">MacBook Pro M1 Max 64GB Mid Upper</a>
                    </h2>
                    <div class="popis">MacBook with 64 GB RAM and M1 Max chip</div>
                    <div class="inzeratycena">39 999 Kč</div>
                    <div class="inzeratylok">Praha<br>110 00</div>
                    <span class="velikost10"> - [11.9. 2026]</span>
                </div>
                <div class="inzeraty">
                    <h2 class="nadpis">
                        <a href="/inzerat/204">MacBook Pro M1 Max 64GB Premium</a>
                    </h2>
                    <div class="popis">MacBook with 64 GB RAM and M1 Max chip</div>
                    <div class="inzeratycena">40 000 Kč</div>
                    <div class="inzeratylok">Praha<br>110 00</div>
                    <span class="velikost10"> - [11.9. 2026]</span>
                </div>
                <div class="inzeraty">
                    <h2 class="nadpis">
                        <a href="/inzerat/205">MacBook Pro M1 Max 64GB Missing Price</a>
                    </h2>
                    <div class="popis">MacBook with 64 GB RAM and M1 Max chip</div>
                    <div class="inzeratylok">Praha<br>110 00</div>
                    <span class="velikost10"> - [11.9. 2026]</span>
                </div>
                <div class="inzeraty">
                    <h2 class="nadpis">
                        <a href="/inzerat/206">MacBook Pro M1 Max 64GB Nonnumeric</a>
                    </h2>
                    <div class="popis">MacBook with 64 GB RAM and M1 Max chip</div>
                    <div class="inzeratycena">Dohoda Kč</div>
                    <div class="inzeratylok">Praha<br>110 00</div>
                    <span class="velikost10"> - [11.9. 2026]</span>
                </div>
                <div class="inzeraty">
                    <h2 class="nadpis">
                        <a href="/inzerat/207">MacBook Pro M1 Max 64GB Foreign Currency</a>
                    </h2>
                    <div class="popis">MacBook with 64 GB RAM and M1 Max chip</div>
                    <div class="inzeratycena">1500 EUR</div>
                    <div class="inzeratylok">Praha<br>110 00</div>
                    <span class="velikost10"> - [11.9. 2026]</span>
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

        self.assertEqual(len(results), 7)
        self.assertEqual(results[0]["price"], "19 999 Kč")
        self.assertEqual(results[0]["price_band"], "budget")
        self.assertEqual(results[1]["price"], "20 000 Kč")
        self.assertEqual(results[1]["price_band"], "mid")
        self.assertEqual(results[2]["price"], "39 999 Kč")
        self.assertEqual(results[2]["price_band"], "mid")
        self.assertEqual(results[3]["price"], "40 000 Kč")
        self.assertEqual(results[3]["price_band"], "premium")
        self.assertEqual(results[4]["price"], "N/A")
        self.assertEqual(results[4]["price_band"], "unknown")
        self.assertEqual(results[5]["price"], "Dohoda Kč")
        self.assertEqual(results[5]["price_band"], "unknown")
        self.assertEqual(results[6]["price"], "1500 EUR")
        self.assertEqual(results[6]["price_band"], "unknown")

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
