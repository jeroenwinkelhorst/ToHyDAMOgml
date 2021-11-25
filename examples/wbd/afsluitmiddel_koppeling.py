# https://gis.stackexchange.com/questions/222315/geopandas-find-nearest-point-in-other-dataframe


from tohydamogml.read_database import read_featureserver
from scipy.spatial import cKDTree
from shapely.geometry import Point, LineString
import numpy as np
import itertools
from operator import itemgetter
import pandas as pd
import os

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
    return gdf.set_index('CODE')

def ckdnearest_points(gdA, gdB):
    nA = np.array(list(gdA.geometry.apply(lambda x: (x.x, x.y))))
    nB = np.array(list(gdB.geometry.apply(lambda x: (x.x, x.y))))
    btree = cKDTree(nB)
    dist, idx = btree.query(nA, k=1)
    gdB_nearest = gdB.iloc[idx].reset_index(drop=True) #.drop(columns="geometry") (removed from middle)
    gdB_nearest.columns = [f"{col}_point" for col in gdB_nearest.columns]
    gdf = pd.concat(
        [
            gdA.reset_index(drop=True),
            gdB_nearest,
            pd.Series(dist, name='dist_point')
        ],
        axis=1)
    return gdf.set_index('CODE')

def closest(row, max_dist):
    min_dist = min([row['dist_line'], row['dist_point']])
    if min_dist > max_dist:
        return "0 - 99 - 0"
    elif min_dist == row['dist_line']:
        return f"{row['CODE_line']} - {row['dist_line']} - line"
    else:
        return f"{row['CODE_point']} - {row['dist_point']} - point"

def closest_geometry(row):
    closest_type = row['type_closest']
    if closest_type == 'line':
        return row['geometry_line']
    elif closest_type == 'point':
        return row['geometry_point']
    else:
        return row['geometry']


def find_closest(gdf_afsluitmiddel, gdf_stuw, gdf_duiker, output_folder, search_dist = 10,
                 export_check=False, export_no_match=False):
    """
    This function calculates the nearest neighbor between afsluitmiddel/stuw & afsluitmiddel/duiker using KD Trees.
    WARNING: KD Trees can make mistakes in finding the NN, because the tree divides the spatial grid in clusters,
    it will only find NN's in the same clusters. Locations at the edge might experience mistakes in assigning the NN.
    - culverts are line elements, they are simplified to a set of points for the purpose of finding the NN

    After finding nearest neighbour between afsluitmiddel/stuw & afsluitmiddel/duiker, the distances of both findings
    are compared. The closest nearest neighbour is assigned as closest structure, unless there is no NN within the
    search_dist. Default search distance = 10.
    """
    closest_stuw = ckdnearest_points(gdf_afsluitmiddel, gdf_stuw)
    closest_duiker = ckdnearest_linestring(gdf_afsluitmiddel, gdf_duiker)

    # join closest stuw & closest duiker
    duiker_cols = [col for col in closest_duiker.columns if col.endswith('_line')]
    all_close = closest_stuw.join(closest_duiker[duiker_cols])

    all_close['temp'] = all_close.apply(lambda x: closest(x, search_dist), axis=1)
    all_close[['code_closest', 'dist_closest', 'type_closest']] = all_close.temp.str.split(" - ", expand=True)
    all_close = all_close.astype({'dist_closest': float})
    all_close['code_closest'] = all_close['code_closest'].replace({'0': None})
    all_close['dist_closest'] = all_close['dist_closest'].replace({'99': None})
    all_close['CODE'] = all_close.index

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    if export_check:
        df_match = all_close.copy()
        df_match.geometry = df_match.apply(lambda x: closest_geometry(x), axis=1)
        df_match.geometry = df_match.buffer(0.1)
        df_match = df_match.drop(columns=['geometry_line', 'geometry_point'])
        df_match.to_file(os.path.join(output_folder, 'kunstwerk_match_check.shp'))
        df_match.to_file(os.path.join(output_folder, 'kunstwerk_match_check.gpkg'), driver='GPKG')

    if export_no_match:
        no_match = all_close.drop(columns=['geometry_line', 'geometry_point'])
        no_match = no_match[no_match['code_closest'].isnull()]
        no_match.to_file(os.path.join(output_folder, 'afsluitmiddel_zonder_koppeling.shp'))
        no_match.to_file(os.path.join(output_folder, 'afsluitmiddel_zonder_koppeling.gpkg'), driver='GPKG')

    dropcols = [col for col in all_close.columns if col.endswith('_point')] + [col for col in all_close.columns if col.endswith('_line')]
    koppeling = all_close.drop(columns=['geometry_line', 'geometry_point', 'temp'] + dropcols)
    koppeling = koppeling[~koppeling['code_closest'].isnull()]
    koppeling.to_file(os.path.join(output_folder, 'afsluitmiddel_koppeling.shp'))
    koppeling.to_file(os.path.join(output_folder, 'afsluitmiddel_koppeling.gpkg'), driver='GPKG')
    return koppeling


if __name__ == '__main__':
    gdf_afsluitmiddel = read_featureserver(
        r'https://maps.brabantsedelta.nl/arcgis/rest/services/Extern/Kunstwerken/FeatureServer', 0)
    gdf_stuw = read_featureserver(
        r'https://maps.brabantsedelta.nl/arcgis/rest/services/Extern/Kunstwerken/FeatureServer', 8)
    gdf_duiker = read_featureserver(
        r'https://maps.brabantsedelta.nl/arcgis/rest/services/Extern/Kunstwerken/FeatureServer', 12)

    closest = find_closest(
        gdf_afsluitmiddel=gdf_afsluitmiddel,
        gdf_stuw=gdf_stuw,
        gdf_duiker=gdf_duiker,
        output_folder='output/afsluitmiddel',
        search_dist=10,
        export_check=True,
        export_no_match=True
    )
