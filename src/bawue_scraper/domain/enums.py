"""LTZF domain enumerations for the BaWue scraper."""

from enum import StrEnum


class Stationstyp(StrEnum):
    """Station types in the legislative process."""

    PREPARL_REGENT = "preparl-regent"
    PREPARL_REGBSL = "preparl-regbsl"
    PARL_INITIATIV = "parl-initiativ"
    PARL_AUSSCHBER = "parl-ausschber"
    PARL_VOLLVLSGN = "parl-vollvlsgn"
    PARL_AKZEPTANZ = "parl-akzeptanz"
    PARL_ABLEHNUNG = "parl-ablehnung"
    POSTPARL_VESJA = "postparl-vesja"
    POSTPARL_GSBLT = "postparl-gsblt"
    POSTPARL_KRAFT = "postparl-kraft"
    SONSTIG = "sonstig"


class Vorgangstyp(StrEnum):
    """Types of legislative proceedings."""

    GG_LAND_PARL = "gg-land-parl"
    BW_EINSATZ = "bw-einsatz"
    SONSTIG = "sonstig"


class Dokumententyp(StrEnum):
    """Types of parliamentary documents."""

    PREPARL_ENTWURF = "preparl-entwurf"
    ENTWURF = "entwurf"
    ANTRAG = "antrag"
    ANFRAGE = "anfrage"
    ANTWORT = "antwort"
    MITTEILUNG = "mitteilung"
    BESCHLUSSEMPF = "beschlussempf"
    STELLUNGNAHME = "stellungnahme"
    GUTACHTEN = "gutachten"
    REDEPROTOKOLL = "redeprotokoll"
    TOPS = "tops"
    TOPS_AEND = "tops-aend"
    TOPS_ERGZ = "tops-ergz"
    SONSTIG = "sonstig"
