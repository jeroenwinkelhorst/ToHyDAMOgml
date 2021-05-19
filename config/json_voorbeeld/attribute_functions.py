"""
Functies specifiek voor waterschap Vallei en Veluwe
"""

import arcpy
import math
import numpy as np
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString
from tohydamogml.domeinen_damo_1_4 import *


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
    return damo_gdf[col_relaties].apply(lambda x: _afsluitmiddel_codegerelateerdobject_apply(x, col_relaties, filegdb=obj["source"]['path'], index_col=obj["index"]['name'], index_col_damo = obj["index"]["src_col"]), axis=1)


def _afsluitmiddel_codegerelateerdobject_apply(x, col_relaties, filegdb, index_col, index_col_damo, damo_objectid=COL_OBJECTID):
    """Get code based on object id
    TODO: improve code
    """

    object_ids = tuple(zip(col_relaties, x))

    for object, id in object_ids:
        if (object[0:-2].lower() in DM_LAYERS.keys()) and not pd.isnull(id):
            if x.name == "KAF-441":
                stop=0
            gdf_tmp = _create_gdf(object[0:-2].lower(), filegdb, index_col, index_col_src=index_col_damo)
            return gdf_tmp[gdf_tmp[damo_objectid] == id].index.values[0]
    return None


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

def _create_gdf(layer, filegdb, index_name: str, index_col_src: str=None):
    """
    Create geodataframe from database.
    Optionally remove object based on statusobjectcode

    filter: dict, {"column_name": [values] }
    filter_type: str, include or exclude
    """
    gdf = gpd.read_file(filegdb, driver="FileGDB", layer=layer)

    # Add original ESRI ID to gdf
    df_arcpy = _table_to_data_frame(filegdb + "//" + layer, prefix=None)
    if COL_OBJECTID == df_arcpy.index.name:
        gdf = gdf.merge(df_arcpy.reset_index().set_index(index_col_src)[COL_OBJECTID].to_frame(), how="left", left_on="CODE",
                        right_index=True)

    gdf.set_index(index_col_src, inplace=True)
    gdf.index.names = [index_name]

    #remove objects without a unique code
    gdf = gdf[gdf.index.notnull()]

    return gdf

def _table_to_data_frame(in_table, input_fields=None, where_clause=None, prefix="rel_"):
    """Function will convert an arcgis table into a pandas dataframe with an object ID index, and the selected
    input fields using an arcpy.da.SearchCursor."""
    OIDFieldName = arcpy.Describe(in_table).OIDFieldName
    if input_fields:
        final_fields = [OIDFieldName] + input_fields
    else:
        final_fields = [field.name for field in arcpy.ListFields(in_table)]
    data = [row for row in arcpy.da.SearchCursor(in_table, final_fields, where_clause=where_clause)]
    fc_dataframe = pd.DataFrame(data, columns=final_fields)
    fc_dataframe = fc_dataframe.set_index(OIDFieldName, drop=True)
    if prefix:
        fc_dataframe = fc_dataframe.add_prefix(prefix)
    return fc_dataframe



# def _codegerelateerdobject(src_gdf=None, obj=None, attr, gdf_src, ref_col_src, gdf_rel, oid_col_rel, return_col_rel):
#     """
#     Gets code of related feature with a relation defined in objectids
#
#     attr: column name attribute
#     gdf_src: source gdf
#     ref_col_src: column with objectid in source
#     gdf_rel: related gdf
#     oid_col_rel: column with objectid in related gdf
#     return_col_rel: column with value to be returned
#     TODO: move this function to custimized functions?
#     """
#     tmp_attr = gdf_src.apply(
#         lambda x: _codegerelateerdobject_apply(x[ref_col_src], gdf_rel, oid_col_rel,
#                                                     return_col_rel), axis=1)
#     return pd.DataFrame(data={attr: tmp_attr})
#
# def _codegerelateerdobject_apply(objectid, gdf_rel, oid_col_rel, return_col_rel):
#     """
#     TODO: move this function to custimized functions?
#     :param objectid:
#     :param gdf_rel:
#     :param oid_col_rel:
#     :param return_col_rel:
#     :return:
#     """
#     gdf_rel = gdf_rel.reset_index()
#     return gdf_rel[gdf_rel[oid_col_rel] == objectid][return_col_rel].values[0]
#
# def _add_geom_gerelateerdobject(self, col_codegerelateerdobject, gemaal_gdf):
#     """Add geometry from related object. Row selection by index"""
#     self.gdf['geometry'] = self.gdf.apply(
#         lambda x: gemaal_gdf.loc[x[col_codegerelateerdobject],'geometry'], axis=1)
#     self.gdf.crs = gemaal_gdf.crs