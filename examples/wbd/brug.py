import geopandas as gpd
from tohydamogml.read_database import read_featureserver
from shapely.ops import snap
from shapely.geometry import Point
from dwarsprofiel_xyz import _make_xyz
import tqdm
import os
import logging
from datetime import datetime

# Make folder for logging
folder = os.path.join('output/brug')
if not os.path.exists(folder):
    os.makedirs(folder)

logging.basicConfig(filename=os.path.join(folder, f'{datetime.today().strftime("%Y%m%d_%H%M")}.log'), level=logging.INFO)
logging.info('Started')

def make_bridge_profile(brug, legger):
    logging.info(f'Begin bridge profile for {brug["CODE"]}')
    line = []
    buffer_size = 0
    while len(line) is 0:
        buffer_size += 0.5
        line = legger[legger.geometry.intersects(brug.geometry.buffer(buffer_size))]
        if buffer_size > 5:
            logging.info(f'No waterline found, skipped bridge: {brug["CODE"]}')
            return None, None
    line = line.iloc[0]
    snapped = snap(brug.geometry, line.geometry, 1)
    dist_normalized = line.geometry.project(snapped, normalized=True)
    bottom = line['WS_BH_BOVENSTROOMS_L'] - dist_normalized * (line['WS_BH_BOVENSTROOMS_L']-line['WS_BH_BENEDENSTROOMS_L'])
    geom_length = line.geometry.length
    dist = dist_normalized * geom_length
    if dist + 5 < geom_length:
        help_dist = dist + 5
    else:
        help_dist = dist - 5
    height = brug['HOOGTEONDE'] - bottom
    if height < 0.1:
        height = 2
    xyz = _make_xyz(row=line, distance_main=dist, distance_help=help_dist,
                    bottom_level=bottom, bottom_width=brug['WS_DOORSTR'],
                    talud_l=0.01, talud_r=0.01, total_depth = height)
    logging.info(f'Made XYZ: {xyz.wkt}')
    new_points = gpd.GeoDataFrame(crs='EPSG:28992')
    for i in range(len(list(xyz.coords))):
        new = gpd.GeoDataFrame(geometry=[Point(list(xyz.coords)[i])],
                               data={'code': [f"{brug['CODE']}_dwp"],
                                     'codeVolgnummer': [i + 1],
                                     'ProfielCode': [f'{brug["CODE"]}_{i + 1}'],
                                     'TypeProfielCode': [3],
                                     'RuwheidsTypeCode': [4],
                                     'RuwheidsWaardeLaag': [75],
                                     'RuwheidsWaardeHoog': [75]})
        new_points = new_points.append(new)
    logging.info('Made Bridge DWP')
    brug_hydamo = gpd.GeoDataFrame(geometry=[brug.geometry],
                                   data={'code': brug['CODE'],
                                         'hoogteonderzijde': [brug['HOOGTEONDE']],
                                         'dwarsprofielcode': [f"{brug['CODE']}_dwp"],
                                         'lengte': [brug['WS_DOORS_1']],
                                         'ruwheidstypecode': [4],
                                         'RuwheidsWaarde': [75],
                                         'intreeverlies': [0],
                                         'uittreeverlies': [0]})
    logging.info('Made Bridge Hydamo')
    return new_points, brug_hydamo


if __name__ == '__main__':
    gdf_legger = read_featureserver(
        r'https://maps.brabantsedelta.nl/arcgis/rest/services/Extern/Legger_Vigerend/FeatureServer', 18)
    gdf_brug = gpd.read_file(r'c:\Users\908367\Box\BH8519 WBD DHYDRO\BH8519 WBD DHYDRO WIP\00_Exchange\Waterschap Brabantse Delta\20210611_aanvullendegegevens\Leveren_aan_RHDHV\dwarsprofielen\Brugprofielen.shp')
    mask = gpd.read_file(r"c:\local\TKI_WBD\aanvullende_data\Aa_of_Weerijs_v2.shp")
    bruggen = gdf_brug[gdf_brug.intersects(mask.unary_union)]

    # problem = make_bridge_profile(bruggen.iloc[5], gdf_legger)

    profiles = gpd.GeoDataFrame(crs='EPSG:28992')
    bridges = gpd.GeoDataFrame(crs='EPSG:28992')
    for i, brug in tqdm.tqdm(bruggen.iterrows(), total=len(bruggen)):
        logging.info(f'i = {i}')
        profile, bridge = make_bridge_profile(brug, gdf_legger)
        if profile is not None:
            profiles = profiles.append(profile)
            bridges = bridges.append(bridge)
        else:
            logging.warning(f'Bridge not added due to lack of data. Code: {brug["CODE"]}')

    profiles.to_file(r'output/brug/dwp_bruggen.gpkg', driver='GPKG')
    bridges.to_file(r'output/brug/bruggen.gpkg', driver='GPKG')
    print(profiles)

