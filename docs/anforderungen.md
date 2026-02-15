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

### Parlamentsdokumentation (PARLIS)

Die Hauptdatenquelle ist die [Parlamentsdokumentation](https://www.landtag-bw.de/de/Dokumente) des Landtags BaWue mit:

- **Drucksachen** — Gesetzentwürfe, Anträge, Anfragen, Beschlussempfehlungen
- **Gesetzesbeschlüsse** — Verabschiedete Gesetze
- **Plenarprotokolle** — Vollständige Sitzungsprotokolle
- **Sach- und Sprechregister** — Indizes nach Thema und Redner

### Zu scrapen

| Datenbereich | Quelle | LTZF-Modell |
|--------------|--------|-------------|
| Gesetzgebungsvorgänge | Drucksachen, Vorgangsübersichten | `Vorgang` + `Station` |
| Tagesordnungen | Plenarsitzungen, Ausschusssitzungen | `Sitzung` + `Top` |
| Ausschussarbeit | Ausschussprotokolle, Beschlussempfehlungen | `Station` (typ: `parl-ausschber`) |
| Dokumente | PDFs der Drucksachen | `Dokument` |

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
