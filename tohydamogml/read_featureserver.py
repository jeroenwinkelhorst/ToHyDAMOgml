"""
Read esri Feature Sevice and keep original objectid

info: https://gdal.org/drivers/vector/esrijson.html
"""

import fiona
import geopandas as gpd
import pandas as pd
from tohydamogml.config import COLNAME_OID

def read_featureservice(url, layer):
    """Read featureservice with fiona to get original objectid. Return geopandas dataframe or pandas dataframe"""
    with fiona.open(url) as collection:
        features = list(collection)
        if next(features)["geometry"] is not None:
            gdf = gpd.GeoDataFrame.from_features(features, crs=get_crs(filegdb, layer))
            gdf[COLNAME_OID] = gdf[COLNAME_OID].astype(int)
            return gdf
        else:
            df = pd.DataFrame.from_records(_yield_table(filegdb, layer))
            df[COLNAME_OID] = df[COLNAME_OID].astype(int)
            return df
    # else:
    #     raise ValueError(f"layer '{layer}' not in layer list: {fiona.listlayers(filegdb)}")


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

if __name__ == '__main__':
    # url = r"https://maps.brabantsedelta.nl/arcgis/rest/services/Extern/Kunstwerken/FeatureServer?f=pjson"
    # test = read_featureservice(url, 'Brug')
    # print(test.head())
    from arcgis.gis import GIS
    from arcgis.features import FeatureLayerCollection
    url = r'https://maps.brabantsedelta.nl/arcgis/rest/services/Extern/Kunstwerken/FeatureServer'
    feature = FeatureLayerCollection(url)
    feature_layer = feature.layers[7]
    query_result1 = feature_layer.query(where='OBJECTID>=0')
    feature.head()