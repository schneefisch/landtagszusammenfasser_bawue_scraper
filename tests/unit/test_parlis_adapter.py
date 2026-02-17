"""Tests for the PARLIS adapter."""

from datetime import date

import pytest
import responses

from bawue_scraper.adapters.parlis_adapter import ParlisAdapter

BASE_URL = "https://parlis.landtag-bw.de/parlis/"
BROWSE_URL = BASE_URL + "browse.tt.json"
REPORT_URL = BASE_URL + "report.tt.html"

SAMPLE_HTML_RECORD = """<html><body>
<div class="efxRecordRepeater">
  <a class="efxZoomShort-Vorgang">Gesetz zur Änderung des Landeshochschulgesetzes</a>
  <dl>
    <dt>Vorgangs-ID:</dt><dd>V-12345</dd>
    <dt>Vorgangstyp:</dt><dd>Gesetzgebung</dd>
    <dt>Initiative:</dt><dd>Fraktion GRÜNE</dd>
    <dt>Aktueller Stand:</dt><dd>Verkündet</dd>
  </dl>
  <a class="fundstellenLinks" href="https://www.landtag-bw.de/resource/blob/12345/doc.pdf">
    Gesetzentwurf    Fraktion GRÜNE  04.02.2026 Drucksache 17/10266   (13 S.)
  </a>
  <a class="fundstellenLinks" href="">
    Erste Beratung   Plenarprotokoll 17/141 05.02.2026
  </a>
  <a class="fundstellenLinks" href="https://www.landtag-bw.de/resource/blob/67890/report.pdf">
    Beschlussempfehlung und Bericht    Ausschuss für Wirtschaft  02.02.2026 Drucksache 17/10210
  </a>
  <script>var url = "/parlis/vorgang/V-12345";</script>
</div>
</body></html>"""

SAMPLE_HTML_TWO_RECORDS = """<html><body>
<div class="efxRecordRepeater">
  <a class="efxZoomShort-Vorgang">Gesetz A</a>
  <dl><dt>Vorgangs-ID:</dt><dd>V-001</dd><dt>Vorgangstyp:</dt><dd>Gesetzgebung</dd><dt>Initiative:</dt><dd>CDU</dd></dl>
  <a class="fundstellenLinks" href="">Gesetzentwurf    CDU  01.01.2026 Drucksache 17/10000</a>
  <script>var url = "/parlis/vorgang/V-001";</script>
</div>
<div class="efxRecordRepeater">
  <a class="efxZoomShort-Vorgang">Gesetz B</a>
  <dl><dt>Vorgangs-ID:</dt><dd>V-002</dd><dt>Vorgangstyp:</dt><dd>Gesetzgebung</dd><dt>Initiative:</dt><dd>SPD</dd></dl>
  <a class="fundstellenLinks" href="">Gesetzentwurf    SPD  02.01.2026 Drucksache 17/10001</a>
  <script>var url = "/parlis/vorgang/V-002";</script>
</div>
</body></html>"""


@pytest.fixture()
def adapter(config, monkeypatch):
    """Create a ParlisAdapter with zero request delay for fast tests."""
    monkeypatch.setattr(config, "parlis_request_delay_s", 0.0)
    return ParlisAdapter(config)


def _mock_search(html, item_count=1):
    """Register standard session + search + report mocks for a single search call."""
    responses.add(responses.GET, BASE_URL, body="<html></html>", status=200)
    responses.add(responses.POST, BROWSE_URL, json={"report_id": "rpt-1", "item_count": item_count}, status=200)
    if item_count > 0:
        responses.add(responses.GET, REPORT_URL, body=html, status=200)


class TestParlisAdapterInit:
    def test_instantiation(self, config):
        adapter = ParlisAdapter(config)
        assert adapter._config is config
        assert adapter._session is not None

    def test_get_detail_raises_not_implemented(self, adapter):
        with pytest.raises(NotImplementedError):
            adapter.get_detail("V-12345")

    @responses.activate
    def test_establish_session_sets_cookies(self, adapter):
        responses.add(
            responses.GET,
            BASE_URL,
            body="<html>PARLIS</html>",
            status=200,
            headers={"Set-Cookie": "JSESSIONID=abc123; Path=/"},
        )
        adapter._establish_session()
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == BASE_URL


class TestSearchQueryConstruction:
    @responses.activate
    def test_search_sends_correct_post_body(self, adapter):
        responses.add(responses.GET, BASE_URL, body="<html></html>", status=200)
        responses.add(
            responses.POST,
            BROWSE_URL,
            json={"report_id": "rpt-123", "item_count": 0},
            status=200,
        )

        adapter.search("Gesetzgebung", date(2026, 1, 1), date(2026, 2, 1))

        post_call = responses.calls[1]
        import json

        body = json.loads(post_call.request.body)
        assert body["action"] == "SearchAndDisplay"
        assert body["search"]["lines"]["l1"] == "17"
        assert body["search"]["lines"]["l2"] == "01.01.2026"
        assert body["search"]["lines"]["l3"] == "01.02.2026"
        assert body["search"]["lines"]["l4"] == "Gesetzgebung"
        assert body["search"]["serverrecordname"] == "vorgang"

    @responses.activate
    def test_search_uses_configured_wahlperiode(self, config, monkeypatch):
        monkeypatch.setenv("WAHLPERIODE", "18")
        config2 = type(config)()
        adapter2 = ParlisAdapter(config2)

        responses.add(responses.GET, BASE_URL, body="<html></html>", status=200)
        responses.add(
            responses.POST,
            BROWSE_URL,
            json={"report_id": "rpt-123", "item_count": 0},
            status=200,
        )

        adapter2.search("Gesetzgebung", date(2026, 1, 1), date(2026, 2, 1))
        import json

        body = json.loads(responses.calls[1].request.body)
        assert body["search"]["lines"]["l1"] == "18"


class TestResultParsing:
    @responses.activate
    def test_parses_vorgang_from_html(self, adapter):
        _mock_search(SAMPLE_HTML_RECORD)

        results = adapter.search("Gesetzgebung", date(2026, 1, 1), date(2026, 2, 1))

        assert len(results) == 1
        vorgang = results[0]
        assert vorgang["titel"] == "Gesetz zur Änderung des Landeshochschulgesetzes"
        assert vorgang["vorgangs_id"] == "V-12345"
        assert vorgang["Initiative"] == "Fraktion GRÜNE"
        assert len(vorgang["fundstellen_parsed"]) == 3

    @responses.activate
    def test_parses_multiple_records(self, adapter):
        _mock_search(SAMPLE_HTML_TWO_RECORDS, item_count=2)

        results = adapter.search("Gesetzgebung", date(2026, 1, 1), date(2026, 2, 1))
        assert len(results) == 2
        assert results[0]["titel"] == "Gesetz A"
        assert results[1]["titel"] == "Gesetz B"

    @responses.activate
    def test_parses_all_fundstelle_types(self, adapter):
        """Verify Gesetzentwurf, Plenarprotokoll, and Ausschuss fundstellen in one search."""
        _mock_search(SAMPLE_HTML_RECORD)

        results = adapter.search("Gesetzgebung", date(2026, 1, 1), date(2026, 2, 1))
        fundstellen = results[0]["fundstellen_parsed"]

        # Gesetzentwurf fundstelle
        assert fundstellen[0]["datum"] == "04.02.2026"
        assert fundstellen[0]["drucksache"] == "17/10266"
        assert fundstellen[0]["station_typ"] == "Gesetzentwurf"
        assert fundstellen[0]["seiten"] == 13
        assert fundstellen[0]["pdf_url"] == "https://www.landtag-bw.de/resource/blob/12345/doc.pdf"

        # Plenarprotokoll fundstelle
        assert fundstellen[1]["datum"] == "05.02.2026"
        assert fundstellen[1]["plenarprotokoll"] == "17/141"
        assert fundstellen[1]["station_typ"] == "Erste Beratung"

        # Ausschuss fundstelle
        assert fundstellen[2]["datum"] == "02.02.2026"
        assert fundstellen[2]["drucksache"] == "17/10210"
        assert fundstellen[2]["station_typ"] == "Beschlussempfehlung und Bericht"
        assert "Ausschuss für Wirtschaft" in fundstellen[2]["ausschuss"]

    @responses.activate
    def test_zero_results_returns_empty_list(self, adapter):
        _mock_search(SAMPLE_HTML_RECORD, item_count=0)

        results = adapter.search("Gesetzgebung", date(2026, 1, 1), date(2026, 2, 1))
        assert results == []


class TestPagination:
    @responses.activate
    def test_fetches_all_pages(self, adapter):
        responses.add(responses.GET, BASE_URL, body="<html></html>", status=200)
        responses.add(
            responses.POST,
            BROWSE_URL,
            json={"report_id": "rpt-123", "item_count": 60},
            status=200,
        )
        # Page 1: 50 records
        inner1 = "\n".join(
            f'<div class="efxRecordRepeater"><a class="efxZoomShort-Vorgang">G{i}</a>'
            f"<dl><dt>Vorgangs-ID:</dt><dd>V-{i:03d}</dd><dt>Vorgangstyp:</dt><dd>Gesetzgebung</dd></dl>"
            f"</div>"
            for i in range(50)
        )
        records_page1 = f"<html><body>{inner1}</body></html>"
        # Page 2: 10 records
        inner2 = "\n".join(
            f'<div class="efxRecordRepeater"><a class="efxZoomShort-Vorgang">G{i}</a>'
            f"<dl><dt>Vorgangs-ID:</dt><dd>V-{i:03d}</dd><dt>Vorgangstyp:</dt><dd>Gesetzgebung</dd></dl>"
            f"</div>"
            for i in range(50, 60)
        )
        records_page2 = f"<html><body>{inner2}</body></html>"
        responses.add(responses.GET, REPORT_URL, body=records_page1, status=200)
        responses.add(responses.GET, REPORT_URL, body=records_page2, status=200)

        results = adapter.search("Gesetzgebung", date(2026, 1, 1), date(2026, 2, 1))

        assert len(results) == 60
        # Verify two GET requests to report URL (two pages)
        report_calls = [c for c in responses.calls if REPORT_URL in c.request.url]
        assert len(report_calls) == 2


class TestDateSubdivision:
    @responses.activate
    def test_subdivides_on_running_status(self, adapter):
        """When initial search returns status=running, subdivide into monthly windows."""
        # First call: establish session
        responses.add(responses.GET, BASE_URL, body="<html></html>", status=200)
        # First search: too large, returns running
        responses.add(
            responses.POST,
            BROWSE_URL,
            json={
                "report_id": "",
                "item_count": 0,
                "sources": {"Star": {"status": "running", "hits": "5000"}},
            },
            status=200,
        )
        # Sub-window 1 (Jan): session + search + report
        responses.add(responses.GET, BASE_URL, body="<html></html>", status=200)
        responses.add(
            responses.POST,
            BROWSE_URL,
            json={"report_id": "rpt-jan", "item_count": 1},
            status=200,
        )
        record_jan = (
            '<html><body><div class="efxRecordRepeater">'
            '<a class="efxZoomShort-Vorgang">Anfrage Jan</a>'
            "<dl><dt>Vorgangs-ID:</dt><dd>V-100</dd></dl>"
            '<script>var url = "/parlis/vorgang/V-100";</script>'
            "</div></body></html>"
        )
        responses.add(responses.GET, REPORT_URL, body=record_jan, status=200)
        # Sub-window 2 (Feb): session + search (empty)
        responses.add(responses.GET, BASE_URL, body="<html></html>", status=200)
        responses.add(
            responses.POST,
            BROWSE_URL,
            json={"report_id": "rpt-feb", "item_count": 0},
            status=200,
        )

        results = adapter.search("Kleine Anfrage", date(2026, 1, 1), date(2026, 2, 28))

        assert len(results) == 1
        assert results[0]["titel"] == "Anfrage Jan"

    @responses.activate
    def test_no_subdivision_on_normal_response(self, adapter):
        """Normal response (with report_id) should NOT trigger subdivision."""
        responses.add(responses.GET, BASE_URL, body="<html></html>", status=200)
        responses.add(
            responses.POST,
            BROWSE_URL,
            json={"report_id": "rpt-123", "item_count": 1},
            status=200,
        )
        record = (
            '<html><body><div class="efxRecordRepeater">'
            '<a class="efxZoomShort-Vorgang">Normal</a>'
            "<dl><dt>Vorgangs-ID:</dt><dd>V-001</dd></dl>"
            '<script>var url = "/parlis/vorgang/V-001";</script>'
            "</div></body></html>"
        )
        responses.add(responses.GET, REPORT_URL, body=record, status=200)

        results = adapter.search("Gesetzgebung", date(2026, 1, 1), date(2026, 2, 1))

        assert len(results) == 1
        # Only 1 POST call (no subdivision)
        post_calls = [c for c in responses.calls if c.request.method == "POST"]
        assert len(post_calls) == 1

    @responses.activate
    def test_subdivision_spans_multiple_months(self, adapter):
        """Subdivision should create monthly windows spanning the full date range."""
        # Session + running response
        responses.add(responses.GET, BASE_URL, body="<html></html>", status=200)
        responses.add(
            responses.POST,
            BROWSE_URL,
            json={
                "report_id": "",
                "item_count": 0,
                "sources": {"Star": {"status": "running", "hits": "4000"}},
            },
            status=200,
        )
        # 3 sub-windows (Jan, Feb, Mar) — all empty
        for _ in range(3):
            responses.add(responses.GET, BASE_URL, body="<html></html>", status=200)
            responses.add(
                responses.POST,
                BROWSE_URL,
                json={"report_id": "", "item_count": 0},
                status=200,
            )

        results = adapter.search("Kleine Anfrage", date(2026, 1, 15), date(2026, 3, 20))

        assert results == []
        # 1 initial + 3 subdivided = 4 POST calls
        post_calls = [c for c in responses.calls if c.request.method == "POST"]
        assert len(post_calls) == 4

    @responses.activate
    def test_session_established_once_even_with_subdivision(self, adapter):
        """_establish_session should be called once per search(), not per sub-window."""
        # Initial search: running → triggers subdivision
        responses.add(responses.GET, BASE_URL, body="<html></html>", status=200)
        responses.add(
            responses.POST,
            BROWSE_URL,
            json={
                "report_id": "",
                "item_count": 0,
                "sources": {"Star": {"status": "running", "hits": "5000"}},
            },
            status=200,
        )
        # Sub-window 1 (Jan): search returns empty (no session GET needed)
        responses.add(
            responses.POST,
            BROWSE_URL,
            json={"report_id": "", "item_count": 0},
            status=200,
        )
        # Sub-window 2 (Feb): search returns empty (no session GET needed)
        responses.add(
            responses.POST,
            BROWSE_URL,
            json={"report_id": "", "item_count": 0},
            status=200,
        )

        adapter.search("Kleine Anfrage", date(2026, 1, 1), date(2026, 2, 28))

        # Only 1 GET to BASE_URL (session establishment), not 3
        session_calls = [c for c in responses.calls if c.request.method == "GET" and c.request.url == BASE_URL]
        assert len(session_calls) == 1
