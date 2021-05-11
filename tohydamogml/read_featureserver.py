"""
Read esri Feature Sevice and keep original objectid

info: https://gdal.org/drivers/vector/esrijson.html
"""

from arcgis.features import FeatureLayerCollection
import geopandas as gpd
import pandas as pd
from tohydamogml.config import COLNAME_OID

def read_featureservice(url, layer_index):
    """Read featureservice with fiona to get original objectid. Return geopandas dataframe or pandas dataframe"""
    collection = FeatureLayerCollection(url)
    wkid = collection.properties['spatialReference']['wkid']
    featureset = collection.layers[layer_index]
    if featureset.properties.geometryField is not None:
        query_all = featureset.query(where=f'{COLNAME_OID}>=0')
        geojson = query_all.to_geojson
        gdf = gpd.read_file(geojson)
        if gdf.crs.to_epsg() != wkid:
            gdf.crs = 'EPSG:'+str(wkid)
        gdf[COLNAME_OID] = gdf[COLNAME_OID].astype(int)
        return gdf
    else:
        #Code adjusted from read_filegdb.py, but might not be needed
        query_all = featureset.query(where=f'{COLNAME_OID}>=0')
        json = query_all.to_geojson
        df = pd.read_json(json) #Doesn't unpack properly! Under df['features'] are all features in another dict
        df[COLNAME_OID] = df[COLNAME_OID].astype(int)
        return df
    # else:
    #     raise ValueError(f"layer '{layer}' not in layer list: {fiona.listlayers(filegdb)}")



if __name__ == '__main__':
    url = r'https://maps.brabantsedelta.nl/arcgis/rest/services/Extern/Kunstwerken/FeatureServer'
    layer = 'stuw'
    layer_index=7
    output = read_featureservice(url, layer_index)
    print(output.head())