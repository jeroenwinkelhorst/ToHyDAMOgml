import geopandas as gpd
from tohydamogml.read_database import read_featureserver
from shapely.ops import snap
from dwarsprofiel_xyz import _make_xyz
import tqdm

def make_bridge_profile(brug, legger):
    line = []
    buffer_size = 0
    while len(line) is 0:
        buffer_size += 0.5
        line = legger[legger.geometry.intersects(brug.geometry.buffer(buffer_size))]
        if buffer_size > 5:
            print(f'No waterline found, skipped bridge: {brug["CODE"]}')
            return None
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
    return xyz

if __name__ == '__main__':
    gdf_legger = read_featureserver(
        r'https://maps.brabantsedelta.nl/arcgis/rest/services/Extern/Legger_Vigerend/FeatureServer', 18)
    gdf_brug = gpd.read_file(r'c:\Users\908367\Box\BH8519 WBD DHYDRO\BH8519 WBD DHYDRO WIP\00_Exchange\Waterschap Brabantse Delta\20210611_aanvullendegegevens\Leveren_aan_RHDHV\dwarsprofielen\Brugprofielen.shp')
    mask = gpd.read_file(r"c:\local\TKI_WBD\aanvullende_data\Aa_of_Weerijs_v2.shp")
    bruggen = gdf_brug[gdf_brug.intersects(mask.unary_union)]

    # problem = make_bridge_profile(bruggen.iloc[28], gdf_legger)

    profiles = []
    for i, brug in tqdm.tqdm(bruggen.iterrows(), total=len(bruggen)):
        profile = make_bridge_profile(brug, gdf_legger)
        profiles.append(profile)

    # profiles = bruggen.apply(lambda bridge: make_bridge_profile(bridge, gdf_legger), axis=1)
    print(profiles)

