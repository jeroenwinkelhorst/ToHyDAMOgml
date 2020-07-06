"""
Read esri filegdb and keep original objectid
"""

import fiona
import geopandas as gpd
import pandas as pd
from tohydamogml.config import COLNAME_OID

def read_filegdb(filegdb, layer):
    """Read filegdb with fiona to get original objectid. Return geopandas dataframe or pandas dataframe"""
    if layer in fiona.listlayers(filegdb):
        features = _yield_features(filegdb, layer)
        if next(features)["geometry"] is not None:
            gdf = gpd.GeoDataFrame.from_features(features, crs=get_crs(filegdb, layer))
            gdf[COLNAME_OID] = gdf[COLNAME_OID].astype(int)
            return gdf
        else:
            df = pd.DataFrame.from_records(_yield_table(filegdb, layer))
            df[COLNAME_OID] = df[COLNAME_OID].astype(int)
            return df
    else:
        raise ValueError(f"layer '{layer}' not in layer list: {fiona.listlayers(filegdb)}")


def _yield_features(path, layer, colname_oid=COLNAME_OID):
    """Read filegdb with fiona to get original objectid"""
    with fiona.open(path, 'r', layer=layer) as f:
        for feature in f:
            feature['properties'][colname_oid] = feature['id']
            yield feature

def _yield_table(path, layer, colname_oid=COLNAME_OID):
    """Read filegdb table with fiona to get original objectid"""
    with fiona.open(path, 'r', layer=layer) as f:
        for feature in f:
            feature['properties'][colname_oid] = feature['id']
            yield feature['properties']

def get_crs(path, layer):
    with fiona.open(path, 'r', layer=layer) as f:
        if type(f.crs) == dict:
            if 'init' in f.crs.keys():
                return f.crs['init']
        return None
