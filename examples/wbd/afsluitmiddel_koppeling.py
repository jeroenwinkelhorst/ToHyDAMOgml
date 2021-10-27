# https://gis.stackexchange.com/questions/222315/geopandas-find-nearest-point-in-other-dataframe


from tohydamogml.read_database import read_featureserver
from scipy.spatial import cKDTree
from shapely.geometry import Point, LineString
import numpy as np
import itertools
from operator import itemgetter
import pandas as pd

def ckdnearest_linestring(gdfA, gdfB): #, gdfB_cols=['Place']):
    A = np.concatenate(
        [np.array(geom.coords) for geom in gdfA.geometry.to_list()])
    B = [np.array(geom[0].coords) for geom in gdfB.geometry.to_list()]
    B_ix = tuple(itertools.chain.from_iterable(
        [itertools.repeat(i, x) for i, x in enumerate(list(map(len, B)))]))
    B = np.concatenate(B)
    ckd_tree = cKDTree(B)
    dist, idx = ckd_tree.query(A, k=1)
    idx = itemgetter(*idx)(B_ix)
    gdfB_rename = gdfB
    gdfB_rename.columns = [f"{col}_line" for col in gdfB_rename]
    gdf = pd.concat(
        [gdfA, gdfB_rename.iloc[[*idx]].reset_index(drop=True),
         pd.Series(dist, name='dist_line')], axis=1)
    return gdf

def ckdnearest_points(gdA, gdB):
    nA = np.array(list(gdA.geometry.apply(lambda x: (x.x, x.y))))
    nB = np.array(list(gdB.geometry.apply(lambda x: (x.x, x.y))))
    btree = cKDTree(nB)
    dist, idx = btree.query(nA, k=1)
    gdB_nearest = gdB.iloc[idx].drop(columns="geometry").reset_index(drop=True)
    gdB_nearest.columns = [f"{col}_near_point" for col in gdB_nearest.columns]
    gdf = pd.concat(
        [
            gdA.reset_index(drop=True),
            gdB_nearest,
            pd.Series(dist, name='dist_point')
        ],
        axis=1)
    return gdf



if __name__ == '__main__':
    gdf_afsluitmiddel = read_featureserver(
        r'https://maps.brabantsedelta.nl/arcgis/rest/services/Extern/Kunstwerken/FeatureServer', 0)

    gdf_stuw = read_featureserver(
        r'https://maps.brabantsedelta.nl/arcgis/rest/services/Extern/Kunstwerken/FeatureServer', 8)
    gdf_duiker = read_featureserver(
        r'https://maps.brabantsedelta.nl/arcgis/rest/services/Extern/Kunstwerken/FeatureServer', 12)

    closest_stuw = ckdnearest_points(gdf_afsluitmiddel, gdf_stuw)
    print(closest_stuw)

    closest_duiker = ckdnearest_linestring(gdf_afsluitmiddel, gdf_duiker)
    print(closest_duiker)