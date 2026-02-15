# Anforderungen: BaWue-Scraper für den Landtagszusammenfasser

## Übersicht

Der Landtagszusammenfasser (LTZF) ist ein Transparenz-Tool, das Informationen zu Landesgesetzen in Deutschland automatisch sammelt, verarbeitet und darstellt. Das System besteht aus drei unabhängigen Komponenten:

1. **Backend/Datenbank** — Zentrale Datenverwaltung und API
2. **Website(s)** — Frontend zur Darstellung für Nutzer
3. **Collectors/Scraper** — Datensammler für verschiedene Landtage

Dieser Scraper ist ein Collector für den **Baden-Württembergischen Landtag** (Parlamentscode: `BW`).

## Referenzen

| Ressource | Link |
|-----------|------|
| LTZF Hauptprojekt | [GitHub](https://github.com/Chrystalkey/landtagszusammenfasser) |
| LTZF Dokumentation | [docs/README.md](https://github.com/Chrystalkey/landtagszusammenfasser/blob/main/docs/README.md) |
| OpenAPI-Spezifikation | [docs/specs/openapi.yml](https://github.com/Chrystalkey/landtagszusammenfasser/blob/main/docs/specs/openapi.yml) |
| Bestehender Collector (Referenz) | [ltzf-collector](https://github.com/Chrystalkey/ltzf-collector/tree/main) |
| CONTRIBUTING | [CONTRIBUTING.md](https://github.com/Chrystalkey/landtagszusammenfasser/blob/main/CONTRIBUTING.md) |
| Landtag BaWue | [landtag-bw.de](https://www.landtag-bw.de/) |
| BaWue Parlamentsdokumentation | [Dokumente](https://www.landtag-bw.de/de/Dokumente) |

## Datenlieferung an das LTZF-Backend

### API-Endpunkte (v2)

Der Scraper liefert Daten über die LTZF Write-API. Relevante Endpunkte für Collectors:

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `PUT /api/v2/vorgang` | PUT | Neuen Gesetzgebungsvorgang einliefern (mit automatischer Deduplizierung) |
| `PUT /api/v2/kalender/{parlament}/{datum}` | PUT | Sitzungen für ein Datum setzen |

Weitere GET-Endpunkte stehen zur Verfügung, um bestehende Daten abzufragen (z.B. zur Vermeidung doppelter Einlieferungen).

### Authentifizierung

- **Header**: `X-API-Key`
- **Scope**: `collector` (erlaubt das Einfügen neuer Vorgänge)
- API-Key wird vom LTZF-Backend-Betreiber bereitgestellt
- Rate-Limit: 256 Requests/Sekunde

### Idempotenz & Deduplizierung

- PUT-Requests sind idempotent
- Das Backend übernimmt die Deduplizierung (z.B. Autoren-Zusammenführung)
- Der Scraper muss sich NICHT um Deduplizierung kümmern
- Das Backend verifiziert NICHT die inhaltliche Korrektheit der Daten

## Benötigte Datenmodelle

### Vorgang (Gesetzgebungsvorgang)

Ein `Vorgang` repräsentiert den gesamten Weg eines Gesetzes durch das Parlament.

**Pflichtfelder:**

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `api_id` | UUID | Eindeutige ID (vom Scraper generiert) |
| `titel` | string | Vollständiger Titel des Vorgangs |
| `typ` | enum | Vorgangstyp (siehe Enumerationen) |
| `wahlperiode` | integer | Wahlperiode (aktuell: 17) |
| `verfassungsaendernd` | boolean | Ob der Vorgang die Verfassung ändert |
| `initiatoren` | array[Autor] | Initiatoren des Vorgangs |
| `stationen` | array[Station] | Stationen des Gesetzgebungsverfahrens |

**Optionale Felder:** `kurztitel`, `ids` (Drucksachennummern etc.), `links`, `lobbyregister`

### Station (Verfahrensstadium)

Jeder Vorgang durchläuft mehrere Stationen.

**Pflichtfelder:**

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `typ` | enum | Stationstyp (siehe Enumerationen) |
| `dokumente` | array[Dokument] | Zugehörige Dokumente |
| `zp_start` | date-time | Zeitpunkt des Stationsbeginns |
| `gremium` | Gremium | Zuständiges Gremium/Ausschuss |

**Optionale Felder:** `titel`, `link`, `schlagworte`, `stellungnahmen`, `trojanergefahr` (1-10)

### Dokument

**Pflichtfelder:**

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `titel` | string | Dokumententitel |
| `volltext` | string | Extrahierter Volltext |
| `hash` | string | Hash des Dokuments |
| `typ` | enum | Dokumententyp (siehe Enumerationen) |
| `zp_modifiziert` | date-time | Letzte Änderung |
| `zp_referenz` | date-time | Referenzdatum |
| `link` | URI | Download-Link |
| `autoren` | array[Autor] | Autoren des Dokuments |

**Optionale Felder:** `drucksnr`, `kurztitel`, `vorwort`, `zusammenfassung`, `meinung` (1-5), `schlagworte`

### Sitzung (Parlamentssitzung)

**Pflichtfelder:**

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `termin` | date-time | Sitzungstermin |
| `gremium` | Gremium | Ausschuss/Plenum |
| `nummer` | integer | Sitzungsnummer |
| `tops` | array[Top] | Tagesordnungspunkte |
| `public` | boolean | Öffentliche Sitzung |

### Gremium (Ausschuss/Plenum)

**Pflichtfelder:**

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `parlament` | enum | `BW` |
| `name` | string | Name des Gremiums |
| `wahlperiode` | integer | Wahlperiode |

### Autor

**Pflichtfelder:**

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `organisation` | string | Organisation (z.B. Fraktion, Ministerium) |

**Optionale Felder:** `person`, `fachgebiet`, `lobbyregister`

### Top (Tagesordnungspunkt)

**Pflichtfelder:**

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `nummer` | string | TOP-Nummer |
| `titel` | string | Titel des Tagesordnungspunkts |

**Optionale Felder:** `vorgang_id` (Verknüpfung zu Vorgängen), `dokumente`

## Enumerationen

### Stationstypen

| Wert | Beschreibung | BaWue-Relevanz |
|------|--------------|----------------|
| `preparl-regent` | Vorparlamentarisch: Regierungsentwurf | Gesetzentwürfe der Landesregierung |
| `preparl-regbsl` | Vorparlamentarisch: Regierungsbeschluss | Kabinettsbeschlüsse |
| `parl-initiativ` | Parlamentarische Initiative | Gesetzentwürfe, Anträge aus dem Landtag |
| `parl-ausschber` | Ausschussberatung | Beratung in Fachausschüssen |
| `parl-vollvlsgn` | Plenarverhandlung | Lesungen im Plenum |
| `parl-akzeptanz` | Annahme | Verabschiedung durch den Landtag |
| `parl-ablehnung` | Ablehnung | Ablehnung durch den Landtag |
| `postparl-vesja` | Ausfertigung | Unterschrift durch Ministerpräsident |
| `postparl-gsblt` | Gesetzblatt | Verkündung im Gesetzblatt |
| `postparl-kraft` | Inkrafttreten | Gesetz tritt in Kraft |
| `sonstig` | Sonstiges | Andere Stationen |

### Vorgangstypen

| Wert | Beschreibung |
|------|--------------|
| `gg-land-parl` | Landesgesetz (parlamentarisch) |
| `bw-einsatz` | BaWue-spezifisch |
| `sonstig` | Sonstiges |

### Dokumententypen

| Wert | Beschreibung |
|------|--------------|
| `preparl-entwurf` | Vorparlamentarischer Entwurf |
| `entwurf` | Gesetzentwurf |
| `antrag` | Antrag |
| `anfrage` | Anfrage |
| `antwort` | Antwort |
| `mitteilung` | Mitteilung |
| `beschlussempf` | Beschlussempfehlung |
| `stellungnahme` | Stellungnahme |
| `gutachten` | Gutachten |
| `redeprotokoll` | Redeprotokoll |
| `tops` | Tagesordnung |
| `tops-aend` | Tagesordnungsänderung |
| `tops-ergz` | Tagesordnungsergänzung |
| `sonstig` | Sonstiges |

## Datenquellen BaWue Landtag

> **Hinweis:** Der Landtag BaWue bietet **keine offizielle API** und **keine Open-Data-Schnittstelle** an. Baden-Württemberg liegt im [Open Data Ranking](https://opendataranking.de/laender/baden-wuerttemberg/) im unteren Drittel. Das Open-Data-Portal [daten.bw](https://www.daten-bw.de/) enthält keine parlamentarischen Daten.

### Übersicht Datenquellen

| Quelle | Typ | Empfehlung |
|--------|-----|------------|
| **PARLIS JSON-Endpunkt** | Undokumentierte API (POST/GET) | **Primärquelle für Vorgänge** — strukturierter als reines Web-Scraping |
| **PARLIS Web-Oberfläche** | Web-Scraping | Fallback / für Daten die der JSON-Endpunkt nicht liefert |
| **landtag-bw.de PDFs** | Download + Textextraktion | Für Volltexte der Drucksachen |
| **ICS-Kalender** | Maschinenlesbar | Für Sitzungstermine |
| **Beteiligungsportal** | Web-Scraping | Ergänzend — vorparlamentarische Entwürfe & Stellungnahmen |
| **Kabinettsberichte (STM)** | Web-Scraping (Fließtext) | Optional — Signalquelle für neue Regierungsentwürfe |
| **Gesetzblatt BaWue** | Web-Suche | Ergänzend — Verkündungen (postparlamentarisch) |

### 1. PARLIS — Undokumentierte JSON-API (Primärquelle)

Das PARLIS-System (`parlis.landtag-bw.de`) bietet neben der Web-Oberfläche einen JSON-Endpunkt, der nicht offiziell dokumentiert ist, aber vom Open-Data-Projekt [dokukratie (OKF)](https://github.com/okfde/dokukratie) produktiv genutzt wird.

**Endpunkte:**

| Endpunkt | Methode | Funktion |
|----------|---------|----------|
| `https://parlis.landtag-bw.de/parlis/browse.tt.json` | POST (JSON) | Suche nach Vorgängen, liefert `report_id` + `item_count` |
| `https://parlis.landtag-bw.de/parlis/report.tt.html` | GET | Ergebnisse abrufen (paginiert via `report_id`, `start`, `chunksize`) |

**Query-Format (POST-Body für browse.tt.json):**

```json
{
    "action": "SearchAndDisplay",
    "report": {
        "rhl": "main",
        "rhlmode": "add",
        "format": "suchergebnis-vorgang-full",
        "mime": "html",
        "sort": "SORT01/D SORT02/D SORT03"
    },
    "search": {
        "lines": {
            "l1": "<wahlperiode>",
            "l2": "<start_date DD.MM.YYYY>",
            "l3": "<end_date DD.MM.YYYY>",
            "l4": "<document_type>"
        },
        "serverrecordname": "vorgang"
    },
    "sources": ["Star"]
}
```

**Ablauf:**

1. Session aufbauen (Cookies/Referer von `parlis.landtag-bw.de/parlis/`)
2. POST an `browse.tt.json` → liefert `report_id` und `item_count`
3. GET auf `report.tt.html?report_id=X&start=0&chunksize=50` → HTML mit Ergebnissen
4. HTML parsen (XPath: `.//div[contains(@class, "efxRecordRepeater")]`)
5. Paginierung: `start` inkrementieren bis alle Ergebnisse abgeholt

**Einschränkungen:**

- Nicht offiziell dokumentiert, kann sich jederzeit ändern
- Ergebnisse kommen als HTML (nicht JSON), müssen geparst werden
- Benötigt Session-Cookie (erst Startseite laden)
- Verfügbare Suchfelder/Dokumenttypen müssen experimentell ermittelt werden

**Technische Referenz:** [okfde/dokukratie BW config](https://github.com/okfde/dokukratie/blob/main/dokukratie/bw.yml)

### 2. PARLIS Web-Oberfläche (Fallback)

Die offizielle Web-Oberfläche: `https://parlis.landtag-bw.de/parlis/`

- Parlamentarische Vorgänge, Drucksachen und Plenarprotokolle ab der 9. Wahlperiode (1984)
- Suchfunktionen: Einfach, Erweitert, Expertenmodus (Bool-Operatoren), Thesaurus
- Ergebnisse als HTML, PDFs zum Download
- Kein Export in maschinenlesbare Formate

### 3. Landtag-Website (landtag-bw.de)

| Bereich | URL | Inhalt |
|---------|-----|--------|
| Drucksachen | `/de/dokumente/drucksachen` | Suchformular + PDF-Downloads |
| Plenarprotokolle | `/de/dokumente/plenarprotokolle` | Protokolle als PDF |
| Gesetzesbeschlüsse | `/de/Gesetzesbeschluesse.html` | Verabschiedete Gesetze |
| Sitzungskalender | ICS-Download verfügbar | `terminkalender.ics` |

- PDFs mit Blob-IDs (`/resource/blob/{id}/...`)
- Kein REST-API, kein RSS/Atom-Feed

### 4. ICS-Kalender (Sitzungstermine)

Der Landtag bietet einen ICS-Kalender-Download für Sitzungstermine an. Dieses maschinenlesbare Format eignet sich als Quelle für `Sitzung`-Daten.

### 5. Drittanbieter-Quellen (ergänzend)

| Quelle | Relevanz | Daten |
|--------|----------|-------|
| [abgeordnetenwatch.de API](https://www.abgeordnetenwatch.de/api) | Begrenzt | Abgeordnete, Abstimmungen — keine Drucksachen/Vorgänge |
| [dokukratie (OKF)](https://github.com/okfde/dokukratie) | Hoch (Referenz) | Funktionierender BW-Scraper, nutzt PARLIS JSON-Endpunkt |
| Beteiligungsportal BaWue | Ergänzend | Gesetzentwürfe im Anhörungsverfahren |

### 6. Staatsministerium & Regierungsquellen

> **Fazit:** Die Quellen des Staatsministeriums (STM) eignen sich **nicht** als Ersatz für PARLIS, da sie keine strukturierten Gesetzgebungsdaten, keine maschinenlesbaren Schnittstellen und keine Drucksachennummern bieten. Zwei Quellen sind jedoch als **Ergänzung** wertvoll.

**Untersuchte STM-Quellen:**

| Quelle | URL | Bewertung |
|--------|-----|-----------|
| STM Aufgaben & Organisation | [stm.baden-wuerttemberg.de/.../aufgaben-und-organisation](https://stm.baden-wuerttemberg.de/de/ministerium/aufgaben-und-organisation) | Nur Organisationsinfos, keine Daten |
| STM Gesetze & Verordnungen | [stm.baden-wuerttemberg.de/.../gesetze-und-verordnungen](https://stm.baden-wuerttemberg.de/de/service/gesetze-und-verordnungen) | Gateway-Seite zu Landesrecht BW und Gesetzblatt |
| Landesrecht BW | [landesrecht-bw.de](https://www.landesrecht-bw.de) | JavaScript-App, keine erkennbare API |
| RSS-Feeds BaWue | [baden-wuerttemberg.de/.../rss](https://www.baden-wuerttemberg.de/de/service/rss) | Themen-Feeds, keiner spezifisch für Gesetzgebung |

#### 6a. Beteiligungsportal (ergänzend — vorparlamentarische Phase)

**URL:** [beteiligungsportal.baden-wuerttemberg.de](https://beteiligungsportal.baden-wuerttemberg.de/de/mitmachen/lp-17)

Das Beteiligungsportal deckt die **vorparlamentarische Phase** ab und enthält Informationen, die in PARLIS nicht verfügbar sind:

- PDF-Downloads von Verordnungs- und Gesetzentwürfen vor der parlamentarischen Einbringung
- 3-Phasen-Prozess: Kommentierung → Ministeriums-Antwort → Beschluss
- Nachhaltigkeits- und Bürokratiebewertungen
- Stellungnahmen von Verbänden und Bürgern

**Einschränkungen:**
- Nur ausgewählte Vorhaben (keine vollständige Abdeckung aller Gesetzentwürfe)
- Kein maschinenlesbarer Zugang (HTML-Scraping erforderlich)

**LTZF-Relevanz:** Stationstypen `preparl-regent` und `preparl-regbsl`

#### 6b. Kabinettsberichte (optionale Signalquelle)

**URL:** [stm.baden-wuerttemberg.de/.../kabinettsberichte](https://stm.baden-wuerttemberg.de/de/themen/regierungskoordination/kabinettsberichte)

Wöchentliche Berichte über Kabinettsbeschlüsse. Können als **Trigger** dienen, um in PARLIS nach neuen Vorgängen zu suchen.

**Einschränkungen:**
- PR-Texte ohne strukturierte Daten (Fließtext)
- Keine Drucksachennummern, keine Verknüpfung zu parlamentarischen Vorgängen
- Keine Volltexte der Gesetzentwürfe

**LTZF-Relevanz:** Kann Hinweise auf neue Vorgänge vom Typ `preparl-regbsl` liefern

#### 6c. Gesetzblatt BaWue (postparlamentarische Phase)

**URL:** [baden-wuerttemberg.de/.../gesetzblatt](https://www.baden-wuerttemberg.de/de/service/alle-meldungen/meldung/pid/gesetzblatt/)

Enthält verkündete Gesetze nach der parlamentarischen Verabschiedung. Web-Suche verfügbar, aber keine API.

**LTZF-Relevanz:** Stationstyp `postparl-gsblt` — Verkündung im Gesetzblatt

### Empfohlene Scraper-Strategie

1. **PARLIS JSON-Endpunkt als Primärquelle** — weniger fragil als reines HTML-Scraping, liefert strukturierte Vorgangsdaten
2. **HTML-Parsing der Ergebnisseiten** für Detail-Extraktion (Stationen, Initiatoren, Dokumentlinks)
3. **PDF-Download + Textextraktion** für Volltexte der Drucksachen
4. **ICS-Kalender** für Sitzungstermine als ergänzende Quelle
5. **dokukratie-Projekt als technische Referenz** — funktionierender BW-Scraper mit bekannten Query-Parametern
6. **Beteiligungsportal** (optional) — für vorparlamentarische Entwürfe und Stellungnahmen, sofern in PARLIS nicht abgedeckt
7. **Kabinettsberichte** (optional) — als Signalquelle für neue Regierungsentwürfe, Trigger für PARLIS-Abfragen

### Zu scrapen

| Datenbereich | Quelle | LTZF-Modell | Priorität |
|--------------|--------|-------------|-----------|
| Gesetzgebungsvorgänge | PARLIS JSON-Endpunkt + Detail-Seiten | `Vorgang` + `Station` | Primär |
| Tagesordnungen | ICS-Kalender, Plenarsitzungen | `Sitzung` + `Top` | Primär |
| Ausschussarbeit | PARLIS, Ausschussprotokolle | `Station` (typ: `parl-ausschber`) | Primär |
| Dokumente | PDFs der Drucksachen (landtag-bw.de) | `Dokument` | Primär |
| Vorparlamentarische Entwürfe | Beteiligungsportal | `Station` (typ: `preparl-regent`), `Dokument` (typ: `preparl-entwurf`) | Ergänzend |
| Kabinettsbeschlüsse | Kabinettsberichte (STM) | Signal für neue `Vorgang`-Suche in PARLIS | Optional |
| Gesetzblatt-Verkündungen | Gesetzblatt BaWue | `Station` (typ: `postparl-gsblt`) | Ergänzend |

## Konfiguration

Der Scraper benötigt folgende Konfiguration (analog zum bestehenden Collector):

| Variable | Beschreibung | Pflicht |
|----------|-------------|---------|
| `LTZF_API_URL` | URL des LTZF-Backends | Ja |
| `LTZF_API_KEY` | API-Key (Scope: collector) | Ja |
| `COLLECTOR_ID` | Eindeutige Collector-ID | Ja |
| `OPENAI_API_KEY` | Für Textextraktion aus PDFs | Optional |

## Referenz: Bestehender Bayern-Scraper

Der [ltzf-collector](https://github.com/Chrystalkey/ltzf-collector/tree/main) enthält einen funktionierenden Scraper für den Bayerischen Landtag als Referenzimplementierung:

- **Sprache:** Python (Poetry)
- **Framework:** Eigenes Scraper-Framework mit abstrakten Basisklassen (`VorgangsScraper`, `SitzungsScraper`)
- **Pattern:** Listing-Pages → Einzelseiten → Datenextraktion → API-Einlieferung
- **Dokumentenverarbeitung:** PDF-Extraktion mit OCR-Fallback (Tesseract)
- **Caching:** Redis für bereits verarbeitete Einträge

### Scraper-Ablauf (nach Referenz)

1. Listing-Page(s) des Parlaments laden
2. URLs einzelner Vorgänge extrahieren
3. Pro Vorgang: Detail-Seite laden und parsen
4. Stationen, Dokumente, Initiatoren extrahieren
5. PDFs herunterladen und Volltext extrahieren
6. `Vorgang`-Objekt zusammenbauen
7. Via `PUT /api/v2/vorgang` an Backend senden

## Generelle Anforderungen

1. **Idempotenz:** Wiederholtes Ausführen darf keine Duplikate erzeugen
2. **Fehlertoleranz:** Einzelne fehlgeschlagene Seiten dürfen nicht den gesamten Scraper stoppen
3. **Rate-Limiting:** Respektierung der Landtags-Website (keine aggressive Abfrage)
4. **Volltext-Extraktion:** PDFs müssen in Volltext konvertiert werden
5. **Korrekte Zuordnung:** Stationstypen und Dokumententypen müssen korrekt auf die LTZF-Enumerationen gemappt werden
6. **Logging:** Nachvollziehbare Logs für Debugging und Monitoring
7. **Konfigurierbarkeit:** Alle externen URLs und Credentials über Umgebungsvariablen/Config
