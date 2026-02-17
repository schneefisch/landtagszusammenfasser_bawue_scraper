"""Mapping from PARLIS terminology to LTZF enum values.

The dictionaries below are fully populated from the architecture document.
The matching functions use case-insensitive substring matching against dictionary keys.
"""

from bawue_scraper.domain.enums import Dokumententyp, Stationstyp, Vorgangstyp

# ---------------------------------------------------------------------------
# Vorgangstyp mapping: PARLIS Vorgangstyp string → LTZF Vorgangstyp
# ---------------------------------------------------------------------------
VORGANGSTYP_MAP: dict[str, Vorgangstyp] = {
    "Gesetzgebung": Vorgangstyp.GG_LAND_PARL,
    "Haushaltsgesetzgebung": Vorgangstyp.GG_LAND_PARL,
    "Volksantrag": Vorgangstyp.GG_LAND_PARL,
    "Antrag": Vorgangstyp.SONSTIG,
    "Antrag der Landesregierung/eines Ministeriums": Vorgangstyp.SONSTIG,
    "Antrag des Rechnungshofs": Vorgangstyp.SONSTIG,
    "Kleine Anfrage": Vorgangstyp.SONSTIG,
    "Große Anfrage": Vorgangstyp.SONSTIG,
    "Mündliche Anfrage": Vorgangstyp.SONSTIG,
    "Aktuelle Debatte": Vorgangstyp.SONSTIG,
    "Anmerkung zur Plenarsitzung": Vorgangstyp.SONSTIG,
    "Ansprache/Erklärung/Mitteilung": Vorgangstyp.SONSTIG,
    "Bericht des Parlamentarischen Kontrollgremiums": Vorgangstyp.SONSTIG,
    "Besetzung externer Gremien": Vorgangstyp.SONSTIG,
    "Besetzung interner Gremien": Vorgangstyp.SONSTIG,
    "Enquetekommission": Vorgangstyp.SONSTIG,
    "EU-Vorlage": Vorgangstyp.SONSTIG,
    "Geschäftsordnung": Vorgangstyp.SONSTIG,
    "Immunitätsangelegenheit": Vorgangstyp.SONSTIG,
    "Mitteilung der Landesregierung/eines Ministeriums": Vorgangstyp.SONSTIG,
    "Mitteilung des Bürgerbeauftragten": Vorgangstyp.SONSTIG,
    "Mitteilung des Landesbeauftragten für den Datenschutz": Vorgangstyp.SONSTIG,
    "Mitteilung des Präsidenten": Vorgangstyp.SONSTIG,
    "Mitteilung des Rechnungshofs": Vorgangstyp.SONSTIG,
    "Petitionen": Vorgangstyp.SONSTIG,
    "Regierungsbefragung": Vorgangstyp.SONSTIG,
    "Regierungserklärung/Regierungsinformation": Vorgangstyp.SONSTIG,
    "Schreiben des Bundesverfassungsgerichts": Vorgangstyp.SONSTIG,
    "Schreiben des Verfassungsgerichtshofs": Vorgangstyp.SONSTIG,
    "Untersuchungsausschuss": Vorgangstyp.SONSTIG,
    "Wahl im Landtag": Vorgangstyp.SONSTIG,
    "Wahlprüfung": Vorgangstyp.SONSTIG,
}

# ---------------------------------------------------------------------------
# Stationstyp mapping: Fundstelle text pattern → LTZF Stationstyp
# Ordered longest-first so "Beschlussempfehlung und Bericht" matches before
# shorter patterns. "Gesetzentwurf" must come after "Erste/Zweite/Dritte Beratung".
# ---------------------------------------------------------------------------
STATIONSTYP_MAP: dict[str, Stationstyp] = {
    "Gesetzentwurf": Stationstyp.PARL_INITIATIV,  # default; override for Landesregierung → PREPARL_REGENT
    "Antrag": Stationstyp.PARL_INITIATIV,
    "Erste Beratung": Stationstyp.PARL_VOLLVLSGN,
    "Zweite Beratung": Stationstyp.PARL_VOLLVLSGN,
    "Dritte Beratung": Stationstyp.PARL_VOLLVLSGN,
    "Beschlussempfehlung und Bericht": Stationstyp.PARL_AUSSCHBER,
    "Ausschussberatung": Stationstyp.PARL_AUSSCHBER,
    "Zustimmung": Stationstyp.PARL_AKZEPTANZ,
    "Annahme": Stationstyp.PARL_AKZEPTANZ,
    "Ablehnung": Stationstyp.PARL_ABLEHNUNG,
    "Ausfertigung": Stationstyp.POSTPARL_VESJA,
    "Gesetzblatt": Stationstyp.POSTPARL_GSBLT,
    "Inkrafttreten": Stationstyp.POSTPARL_KRAFT,
}

# Sorted keys longest-first for greedy matching
_STATIONSTYP_KEYS_SORTED = sorted(STATIONSTYP_MAP.keys(), key=len, reverse=True)

# ---------------------------------------------------------------------------
# Dokumententyp mapping: document context → LTZF Dokumententyp
# ---------------------------------------------------------------------------
DOKUMENTENTYP_MAP: dict[str, Dokumententyp] = {
    "Gesetzentwurf": Dokumententyp.ENTWURF,  # override for vorparlamentarisch → PREPARL_ENTWURF
    "Antrag": Dokumententyp.ANTRAG,
    "Kleine Anfrage": Dokumententyp.ANFRAGE,
    "Große Anfrage": Dokumententyp.ANFRAGE,
    "Mündliche Anfrage": Dokumententyp.ANFRAGE,
    "Antwort": Dokumententyp.ANTWORT,
    "Stellungnahme": Dokumententyp.STELLUNGNAHME,
    "Beschlussempfehlung": Dokumententyp.BESCHLUSSEMPF,
    "Plenarprotokoll": Dokumententyp.REDEPROTOKOLL,
    "Mitteilung": Dokumententyp.MITTEILUNG,
}

_DOKUMENTENTYP_KEYS_SORTED = sorted(DOKUMENTENTYP_MAP.keys(), key=len, reverse=True)


def map_vorgangstyp(parlis_typ: str) -> Vorgangstyp:
    """Map a PARLIS Vorgangstyp string to the LTZF Vorgangstyp enum.

    Args:
        parlis_typ: The Vorgangstyp string from PARLIS.

    Returns:
        The corresponding LTZF Vorgangstyp, or SONSTIG if no match.
    """
    return VORGANGSTYP_MAP.get(parlis_typ, Vorgangstyp.SONSTIG)


def map_stationstyp(fundstelle_text: str, initiator: str | None = None) -> Stationstyp:
    """Map a Fundstelle text to the LTZF Stationstyp enum.

    Uses case-insensitive substring matching against known patterns, longest first.
    If the station is a Gesetzentwurf from the Landesregierung, maps to PREPARL_REGENT.

    Args:
        fundstelle_text: The raw Fundstelle text from PARLIS.
        initiator: Optional initiator string for context-dependent mapping.

    Returns:
        The corresponding LTZF Stationstyp, or SONSTIG if no match.
    """
    text_lower = fundstelle_text.lower()
    for key in _STATIONSTYP_KEYS_SORTED:
        if key.lower() in text_lower:
            # Special case: Gesetzentwurf from Landesregierung → PREPARL_REGENT
            if key == "Gesetzentwurf" and initiator and "Landesregierung" in initiator:
                return Stationstyp.PREPARL_REGENT
            return STATIONSTYP_MAP[key]
    return Stationstyp.SONSTIG


def map_dokumententyp(context: str, is_vorparlamentarisch: bool = False) -> Dokumententyp:
    """Map a document context string to the LTZF Dokumententyp enum.

    Args:
        context: The document context (e.g. station type, document title keywords).
        is_vorparlamentarisch: If True and context is Gesetzentwurf, use PREPARL_ENTWURF.

    Returns:
        The corresponding LTZF Dokumententyp, or SONSTIG if no match.
    """
    context_lower = context.lower()
    for key in _DOKUMENTENTYP_KEYS_SORTED:
        if key.lower() in context_lower:
            if key == "Gesetzentwurf" and is_vorparlamentarisch:
                return Dokumententyp.PREPARL_ENTWURF
            return DOKUMENTENTYP_MAP[key]
    return Dokumententyp.SONSTIG
