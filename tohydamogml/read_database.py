"""
Read esri filegdb and keep original objectid
"""

from arcgis.features import FeatureLayerCollection
import fiona
import geopandas as gpd
import pandas as pd
from tohydamogml.config import COLNAME_OID
from shapely.geometry import Point, LineString


def read_featureserver(url, layer_index):
    """Read featureservice with fiona to get original objectid. Return geopandas dataframe or pandas dataframe"""
    collection = FeatureLayerCollection(url)
    wkid = collection.properties['spatialReference']['wkid']
    featureset = collection.layers[int(layer_index)]
    if featureset.properties.geometryField is not None:
        fieldnames = [field['name'] for field in featureset.properties.fields]
        if COLNAME_OID in fieldnames:
            col = COLNAME_OID
        else:
            cols = [name for name in fieldnames if name.startswith(COLNAME_OID)]
            if len(cols) == 0:
                raise ValueError(f"Can't find column starting with '{COLNAME_OID}', thus unable to query dataset")
            else:
                col = cols[0]
        query_all = featureset.query(where=f'{col}>=0')
        try:
            geojson = query_all.to_geojson
            gdf = gpd.read_file(geojson)
            if gdf.crs['init'] != wkid:
                gdf.crs = 'EPSG:' + str(wkid)
        except:
            # For some reason, the geojson created from the esri dataset doesn't always get read by geopandas/fiona.
            # If the geojson method fails, a manual operation is used to create the geodataframe anyway.
            sdf = query_all.sdf
            sdf['geometry'] = sdf.apply(lambda x: LineString([Point(xy[0], xy[1]) for xy in x['SHAPE']['paths'][0]]), axis=1)
            gdf = gpd.GeoDataFrame(sdf)
            gdf.crs = 'EPSG:'+str(wkid)
        gdf[COLNAME_OID] = gdf[col].astype(int)
        return gdf
    else:
        #Code adjusted from read_filegdb, but might not be needed
        query_all = featureset.query(where=f'{COLNAME_OID}>=0')
        json = query_all.to_geojson
        df = pd.read_json(json) #Doesn't unpack properly! Under df['features'] are all features in another dict
        df[COLNAME_OID] = df[COLNAME_OID].astype(int)
        return df


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

if __name__ == '__main__':
    a = read_featureserver('https://maps.brabantsedelta.nl/arcgis/rest/services/Extern/Kunstwerken/FeatureServer', '14')
    mask = gpd.read_file(r"c:\local\TKI_WBD\aanvullende_data\Aa_of_Weerijs_v2.shp")
    gdf = a[a.intersects(mask.unary_union)]
    gdf.to_file(r'c:\Users\908367\Box\BH8519 WBD DHYDRO\BH8519 WBD DHYDRO WIP\04_GIS\kopie_server\Cat_A_Waterloop_Aa_of_Weerijs.shp')
    gdf.to_file(r'c:\Users\908367\Box\BH8519 WBD DHYDRO\BH8519 WBD DHYDRO WIP\04_GIS\kopie_server\Cat_A_Waterloop_Aa_of_Weerijs.gpkg', driver='GPKG')
