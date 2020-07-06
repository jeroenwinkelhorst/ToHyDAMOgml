"""
Functies specifiek voor waterschap Vallei en Veluwe
"""

import math
import numpy as np
import geopandas as gpd
import pandas as pd
import fiona
from shapely.geometry import LineString
from tohydamogml.domeinen_damo_1_4 import *
from tohydamogml.read_filegdb import read_filegdb

# Columns in DAMO to search for id of related object
DM_COL_CODEGERELATEERD_OBJECT = [
    # 'COUPUREID',
    'DUIKERSIFONHEVELID',
    # 'FLEXIBELEWATERKERINGID',
    'GEMAALID',
    # 'SLUISID',
    'STUWID',
    # 'REGENWATERBUFFERCOMPARTIMENTID',
    # 'TUNNELID',
    # 'VISPASSAGEID'
]

DM_LAYERS = {
    "hydroobject": "HydroObject",
    "stuw": "Stuw",
    "afsluitmiddel": "Afsluitmiddel",
    "doorstroomopening": "Doorstroomopening",
    "duikersifonhevel": "DuikerSifonHevel",
    "gemaal": "Gemaal",
    "brug": "Brug",
    "bodemval": "Bodemval",
    "aquaduct": "Aquaduct",
    "afvoergebied": "AfvoergebiedAanvoergebied",

}

COL_OBJECTID = "OBJECTID"


def stuw_kruinbreedte(damo_gdf=None, obj=None, damo_kruinbreedte="KRUINBREEDTE",
                      damo_doorstroombreedte="DOORSTROOMBREEDTE",
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


def obj_soortmateriaal(damo_gdf=None, obj=None, damo_soortmateriaal="SOORTMATERIAAL"):
    return damo_gdf.apply(lambda x: _obj_get_soortmateriaal(x[damo_soortmateriaal]), axis=1)


def _obj_get_soortmateriaal(materiaalcode):
    """Return Strickler Ks waarde
    Bron: Ven te Chow - Open channel hydraulics tbl 5-6
    TODO: omschrijven naar dictionary in config"""
    if materiaalcode in MATERIAALKUNSTWERK.keys():
        if MATERIAALKUNSTWERK[materiaalcode] == "beton":
            return 75
        if MATERIAALKUNSTWERK[materiaalcode] == "gewapend beton":
            return 75
        if MATERIAALKUNSTWERK[materiaalcode] == "metselwerk":
            return 65
        if MATERIAALKUNSTWERK[materiaalcode] == "metaal":
            return 80
        if MATERIAALKUNSTWERK[materiaalcode] == "aluminium":
            return 80
        if MATERIAALKUNSTWERK[materiaalcode] == "ijzer":
            return 80
        if MATERIAALKUNSTWERK[materiaalcode] == "gietijzer":
            return 75
        if MATERIAALKUNSTWERK[materiaalcode] == "PVC":
            return 80
        if MATERIAALKUNSTWERK[materiaalcode] == "gegolfd plaatstaal":
            return 65
        if MATERIAALKUNSTWERK[materiaalcode] == "asbestcement":
            return 110
    return 999


def afsluitmiddel_codegerelateerdobject(damo_gdf=None, obj=None, col_relaties=DM_COL_CODEGERELATEERD_OBJECT):
    """Get code of related object. Is more the one code is defined, None value is returned
    TODO: improve code
    """
    code_src = []
    code_rel = []
    for objectname in col_relaties:
        if DM_LAYERS[objectname[0:-2].lower()] in fiona.listlayers(obj["source"]['path']):
            gdf_tmp = _create_gdf(DM_LAYERS[objectname[0:-2].lower()], obj["source"]['path'],
                                  index_name=obj["index"]['name'], index_col_src=obj["index"]["src_col"])
            for index, value in damo_gdf[objectname].dropna().iteritems():
                code_src.append(index)
                code_rel.append(gdf_tmp[gdf_tmp['OBJECTID'].astype(int) == int(value)].index.values[0])
    damo_gdf["relaties"] = pd.DataFrame(data=code_rel, index=code_src)
    return damo_gdf["relaties"]


def brug_pt_to_line(damo_gdf=None):
    return damo_gdf.apply(lambda x: _brug_profile_geometry(x, lijn_lengte="WS_LENGTEBRUG", rotate_degree=0), axis=1)


def brug_profile_geometry(damo_gdf=None):
    return damo_gdf.apply(lambda x: _brug_profile_geometry(x, lijn_lengte="WS_BREEDTEBRUG", rotate_degree=90), axis=1)


def _brug_profile_geometry(row, direction="RICHTING", lijn_lengte="WS_LENGTEBRUG", rotate_degree=0, default_width=1,
                           default_dir=0):
    """
    Convert bridge point to line
    direction in degrees"""
    dir = math.radians(row[direction] + rotate_degree) if not pd.isnull(row[direction]) else math.radians(
        default_dir + rotate_degree)
    length = row[lijn_lengte] if not pd.isnull(row[lijn_lengte]) else default_width

    dx = math.cos(dir) * 0.5 * length
    dy = math.sin(dir) * 0.5 * length

    return LineString([(row.geometry.x - float(dx), row.geometry.y - float(dy)),
                       (row.geometry.x + float(dx), row.geometry.y + float(dy))])


def _create_gdf(layer, filegdb, index_name: str, index_col_src: str = None):
    """
    Create geodataframe from database.
    Optionally remove object based on statusobjectcode

    filter: dict, {"column_name": [values] }
    filter_type: str, include or exclude
    """
    gdf = read_filegdb(filegdb, layer=layer)
    gdf.set_index(index_col_src, inplace=True)
    gdf.index.names = [index_name]

    # remove objects without a unique code
    gdf = gdf[gdf.index.notnull()]

    return gdf
