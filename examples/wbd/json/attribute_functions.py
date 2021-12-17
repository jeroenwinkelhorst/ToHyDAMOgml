"""
Functies specifiek voor waterschap Vallei en Veluwe
"""

# import arcpy
import math
import numpy as np
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Point
from tohydamogml.domeinen_damo_1_4 import *
from tohydamogml.config import *
import logging
import shapely


# Columns in DAMO to search for id of related object
DM_COL_CODEGERELATEERD_OBJECT = ['COUPUREID', 'DUIKERSIFONHEVELID', 'FLEXIBELEWATERKERINGID',
                                                          'GEMAALID', 'SLUISID', 'STUWID',
                                                          'REGENWATERBUFFERCOMPARTIMENTID', 'TUNNELID',
                                                          'VISPASSAGEID']

DM_LAYERS = {
                "hydroobject": "HydroObject",
                "stuw": "Stuw",
                "afsluitmiddel": "Afsluitmiddel",
                "doorstroomopening":"Doorstroomopening",
                "duikersifonhevel": "DuikerSifonHevel",
                "gemaal": "Gemaal",
                "brug": "Brug",
                "bodemval": "Bodemval",
                "aquaduct": "Aquaduct",
                "afvoergebied": "AfvoergebiedAanvoergebied"
}

COL_OBJECTID = "OBJECTID"


def stuw_code(damo_gdf=None, obj=None):
    """"
    Zet naam van TYPESTUW om naar attribuutwaarde
    """
    data = [_stuw_code(name) for name in damo_gdf['SOORTSTUW']]
    df = pd.Series(data=data, index=damo_gdf.index)
    return df


def _stuw_code(current_name=None):
    """"
    Zoekt door TYPESTUW naar de naam van het stuwtype, geeft attribuut waarde uit DAMO
    """
    if current_name not in TYPESTUW.values():
        return 999
    for i, name in TYPESTUW.items():
        if name == current_name:
            return i


def stuw_regelbaarheid(damo_gdf=None, obj=None):
    """"
    Zet naam van TYPEREGELBAARHEID om naar attribuutwaarde
    """
    data = [_stuw_regelbaarheid(name) for name in damo_gdf['SOORTREGELBAARHEID']]
    df = pd.Series(data=data, index=damo_gdf.index)
    return df


def _stuw_regelbaarheid(current_name=None):
    """"
    Zoekt door TYPEREGELBAARHEID naar de naam van het stuwtype, geeft attribuut waarde uit DAMO
    """
    if current_name not in TYPEREGELBAARHEID.values():
        return 99
    for i, name in TYPEREGELBAARHEID.items():
        if name == current_name:
            return i


def stuw_kruinbreedte(damo_gdf=None, obj=None, damo_kruinbreedte="KRUINBREEDTE", damo_doorstroombreedte="DOORSTROOMBREEDTE",
                      damo_kruinvorm="WS_KRUINVORM"):
    """
    als KRUINBREEDTE is NULL en WS_KRUINVORM =3 (rechthoek) dan KRUINBREEDTE = DOORSTROOMBREEDTE
    """
    return damo_gdf.apply(
        lambda x: _stuw_get_kruinbreedte_rechthoek(x[damo_kruinbreedte], x[damo_kruinvorm], x[damo_doorstroombreedte]),
        axis=1)


def stuw_laagstedoorstroombreedte(damo_gdf=None, obj=None, damo_doorstroombreedte="DOORSTROOMBREEDTE",
                                  damo_kruinvorm="WS_KRUINVORM"):
    """
    als LAAGSTEDOORSTROOMHOOGTE is NULL en WS_KRUINVORM =3 (rechthoek) dan LAAGSTEDOORSTROOMBREEDTE = DOORSTROOMBREEDTE
    """
    return damo_gdf.apply(
        lambda x: _stuw_get_laagstedoorstroombreedte_rechthoek(x[damo_kruinvorm], x[damo_doorstroombreedte]), axis=1)


def _stuw_get_kruinbreedte_rechthoek(kruinbreedte: float, kruinvorm: float, doorstroombreedte: float,
                                     kruinvorm_rechthoek=[3.0]):
    """
    als KRUINBREEDTE is NULL en WS_KRUINVORM =3 (rechthoek) dan KRUINBREEDTE = DOORSTROOMBREEDTE
    """
    if np.isnan(kruinbreedte):
        if kruinvorm in kruinvorm_rechthoek:
            return doorstroombreedte
    else:
        return kruinbreedte


def _stuw_get_laagstedoorstroombreedte_rechthoek(kruinvorm: float, doorstroombreedte: float, kruinvorm_rechthoek=[3.0]):
    """
    als LAAGSTEDOORSTROOMHOOGTE is NULL en WS_KRUINVORM =3 (rechthoek) dan LAAGSTEDOORSTROOMBREEDTE = DOORSTROOMBREEDTE
    """

    if kruinvorm in kruinvorm_rechthoek:
        return doorstroombreedte
    else:
        return np.nan

def duikerhevelsifon_soortkokervormigeconstructiecode(damo_gdf=None, obj=None, damo_typekruising="TYPEKRUISING"):
    return damo_gdf.apply(lambda x: _duikerhevelsifon_get_skvccode(x[damo_typekruising]), axis=1)

def _duikerhevelsifon_get_skvccode(damo_typekruising):
    """
    Convert DAMO Typekruising to soortkokervormigeconstructiecode
    """
    if TYPEKRUISING[damo_typekruising] == "duiker":
        return 1
    elif TYPEKRUISING[damo_typekruising] == "hevel":
        return 2
    elif TYPEKRUISING[damo_typekruising] == "sifon":
        return 3
    else:
        return 999

def duikersifonhevel_vorm(damo_gdf=None, obj=None):
    """"
    Zet naam van VORMKOKER om naar attribuutwaarde
    """
    data = [_duikersifonhevel_vorm(name) for name in damo_gdf['VORMKOKER']]
    df = pd.Series(data=data, index=damo_gdf.index)
    return df


def _duikersifonhevel_vorm(current_vorm):
    """"
    Zoekt door VORMKOKER naar de naam van de vorm, geeft attribuut waarde uit DAMO
    """
    if current_vorm not in VORMKOKER.values():
        return 999
    for i, vorm in VORMKOKER.items():
        if vorm == current_vorm:
            return i


def obj_soortmateriaal(damo_gdf=None, obj=None, damo_soortmateriaal="SOORTMATERIAAL"):
    return damo_gdf.apply(lambda x: _obj_get_soortmateriaal(x[damo_soortmateriaal]), axis=1)

def _obj_get_soortmateriaal(materiaalcode):
    """Return Strickler Ks waarde
    Bron: Ven te Chow - Open channel hydraulics tbl 5-6"""
    if materiaalcode not in RUWHEID_VEN_TE_CHOW.keys():
        return 999
    else:
        return RUWHEID_VEN_TE_CHOW[materiaalcode]


def afsluitmiddel_soort(damo_gdf=None, obj=None):
    """"
    Zet naam van SOORTAFSLUITMIDDEL om naar attribuutwaarde
    """
    data = [_afsluitmiddel_soort(name) for name in damo_gdf['SOORTAFSLUITMIDDEL']]
    df = pd.Series(data=data, index=damo_gdf.index)
    return df


def _afsluitmiddel_soort(current_soort):
    """"
    Zoekt door SOORTAFSLUITMIDDEL naar de naam van de vorm, geeft attribuut waarde uit DAMO
    """
    if current_soort not in SOORTAFSLUITMIDDEL.values():
        return 99
    for i, soort in SOORTAFSLUITMIDDEL.items():
        if soort == current_soort:
            return i

def afsluitmiddel_regelbaarheid(damo_gdf=None, obj=None):
    """"
    Zet naam van AFSLUITREGELBAARHEID om naar attribuutwaarde
    """
    data = [_afsluitmiddel_regelbaarheid(name) for name in damo_gdf['SOORTREGELBAARHEID']]
    df = pd.Series(data=data, index=damo_gdf.index)
    return df


def _afsluitmiddel_regelbaarheid(current_soort):
    """"
    Zoekt door TYPEREGELBAARHEID naar de naam van het soort regelbaarheid, geeft attribuut waarde uit DAMO
    """
    if current_soort not in TYPEREGELBAARHEID.values():
        return 99
    for i, soort in TYPEREGELBAARHEID.items():
        if soort == current_soort:
            return i

def gemaal_rename_index(damo_gdf=None, obj=None):
    """
    Hernoem gemaal index met de prefix: "GEM_"
    """
    return ["GEM_"+code for code in damo_gdf.index]

def dwp_rename_index_boven(damo_gdf=None, obj=None):
    """
    Hernoem DWP index op basis van legger waterloop code met prefix "DWP_boven"
    """
    return [f"DWP_boven_{code}" for code in damo_gdf.index]

def dwp_rename_index_beneden(damo_gdf=None, obj=None):
    """
    Hernoem DWP index op basis van legger waterloop code met prefix "DWP_boven"
    """
    return [f"DWP_beneden_{code}" for code in damo_gdf.index]

def brug_pt_to_line(damo_gdf=None, obj=None):
    return damo_gdf.apply(lambda x: _brug_profile_geometry(x, lijn_lengte="WS_LENGTEBRUG" ,rotate_degree=0), axis=1)


def brug_profile_geometry(damo_gdf=None, obj=None):
    return damo_gdf.apply(lambda x: _brug_profile_geometry(x, lijn_lengte="WS_BREEDTEBRUG", rotate_degree=90), axis=1)


def _brug_profile_geometry(row, direction="RICHTING", lijn_lengte="WS_LENGTEBRUG", rotate_degree=0, default_width=1, default_dir=0):
    """
    Convert bridge point to line
    direction in degrees"""
    dir = math.radians(row[direction]+rotate_degree) if not pd.isnull(row[direction]) else math.radians(default_dir+rotate_degree)
    length = row[lijn_lengte] if not pd.isnull(row[lijn_lengte]) else default_width

    dx = math.cos(dir) * 0.5 * length
    dy = math.sin(dir) * 0.5 * length

    return LineString([(row.geometry.x-float(dx), row.geometry.y-float(dy)),(row.geometry.x+float(dx), row.geometry.y+float(dy))])

def dwp_upstream(damo_gdf=None, obj=None):
    return damo_gdf.apply(lambda x: _make_dwp(x, 'upstream', profile_dist=5), axis=1)

def dwp_downstream(damo_gdf=None, obj=None):
    return damo_gdf.apply(lambda x: _make_dwp(x, 'downstream', profile_dist=5), axis=1)

def _make_dwp(row, up_or_down: str = 'upstream', profile_dist: float = 5):
    width = row['WS_BODEMBREEDTE_L'] + 2 * row['WS_TALUD_LINKS_L'] + 2 * row['WS_TALUD_RECHTS_L']
    l = row['geometry'].length
    logging.info(f'DWP maken: {up_or_down}, {row["CODE"]}, lengte: {l}, breedte: {width}')
    if l > (profile_dist * 2 + 1):
        dist1 = profile_dist
        dist2 = profile_dist - 1
    else:
        dist1 = l * 0.2
        dist2 = l * 0.4
    if up_or_down.lower().startswith('down'):
        dist1 = dist1 * -1
        dist2 = dist2 * -1
    if math.isnan(width):
        width = 6
        logging.info(f"Normgeparametriseerdprofiel maken: {row['CODE']} er kon geen breedte gemaakt worden, geometrie wordt 6 meter breed")
    point1 = row['geometry'].interpolate(dist1)
    point2 = row['geometry'].interpolate(dist2)
    baseline = LineString([point1, point2])
    left = baseline.parallel_offset(width/2, 'left')
    right = baseline.parallel_offset(width/2, 'right')
    left_point = left.coords[0]
    right_point = right.coords[-1]
    profile_line = LineString([left_point, right_point])
    return profile_line

def insteek_hoogte_bovenstrooms(damo_gdf=None, obj=None):
    data = [bodem + 2 for bodem in damo_gdf['WS_BH_BOVENSTROOMS_L']]
    df = pd.Series(data=data, index=damo_gdf.index)
    return df


def insteek_hoogte_benedenstrooms(damo_gdf=None, obj=None):
    data = [bodem + 2 for bodem in damo_gdf['WS_BH_BENEDENSTROOMS_L']]
    df = pd.Series(data=data, index=damo_gdf.index)
    return df

def replace_crestlevel(damo_gdf=None, obj=None):
    col_sp = 'rel_Streef P'
    data = []
    for i, row in damo_gdf.iterrows():
        if not math.isnan(row[col_sp]):
            data.append(row[col_sp] - 0.05)
        else:
            data.append(row['LAAGSTEDOORSTROOMHOOGTE'])
    df = pd.Series(data=data, index=damo_gdf.index)
    return df

def rand_index(damo_gdf=None, obj=None):
    return ["rand_"+str(i) for i in damo_gdf.index]


if __name__ == '__main__':
    import sys
    sys.path.append('../../..')
    from tohydamogml.read_database import read_featureserver
    waterlopen = read_featureserver('https://maps.brabantsedelta.nl/arcgis/rest/services/Extern/Legger_Vigerend/FeatureServer', '18')
    # waterlopen = read_featureserver('https://maps.brabantsedelta.nl/arcgis/rest/services/Extern/Kunstwerken/FeatureServer', '14')
    test = waterlopen.iloc[0]
    print(test)
