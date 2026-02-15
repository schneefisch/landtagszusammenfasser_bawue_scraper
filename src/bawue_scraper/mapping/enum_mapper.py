"""Mapping from PARLIS terminology to LTZF enum values.

The dictionaries below are fully populated from the architecture document.
The regex-based matching functions that use them are stubbed for TDD implementation.
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
    "Kleine Anfrage": Vorgangstyp.SONSTIG,
    "Große Anfrage": Vorgangstyp.SONSTIG,
    "Mündliche Anfrage": Vorgangstyp.SONSTIG,
    "Aktuelle Debatte": Vorgangstyp.SONSTIG,
    "Regierungserklärung/Regierungsinformation": Vorgangstyp.SONSTIG,
    "Untersuchungsausschuss": Vorgangstyp.SONSTIG,
}

# ---------------------------------------------------------------------------
# Stationstyp mapping: Fundstelle text pattern → LTZF Stationstyp
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

    Uses regex matching against known patterns. If the station is a Gesetzentwurf
    from the Landesregierung, maps to PREPARL_REGENT instead of PARL_INITIATIV.

    Args:
        fundstelle_text: The raw Fundstelle text from PARLIS.
        initiator: Optional initiator string for context-dependent mapping.

    Returns:
        The corresponding LTZF Stationstyp, or SONSTIG if no match.
    """
    # todo: implement regex matching against STATIONSTYP_MAP keys
    # todo: handle Gesetzentwurf from Landesregierung → PREPARL_REGENT
    return Stationstyp.SONSTIG


def map_dokumententyp(context: str, is_vorparlamentarisch: bool = False) -> Dokumententyp:
    """Map a document context string to the LTZF Dokumententyp enum.

    Args:
        context: The document context (e.g. station type, document title keywords).
        is_vorparlamentarisch: If True and context is Gesetzentwurf, use PREPARL_ENTWURF.

    Returns:
        The corresponding LTZF Dokumententyp, or SONSTIG if no match.
    """
    # todo: implement regex matching against DOKUMENTENTYP_MAP keys
    # todo: handle vorparlamentarisch Gesetzentwurf → PREPARL_ENTWURF
    return Dokumententyp.SONSTIG
