import geopandas as gpd
from tohydamogml.read_database import read_featureserver
from shapely.ops import snap

def determine_bottom_height(brug, legger):
    line = []
    buffer_size = 0
    while len(line) is 0:
        buffer_size += 0.5
        line = legger[legger.geometry.intersects(brug.geometry.buffer(buffer_size))]
    line = line.iloc[0]
    snapped = snap(brug.geometry, line.geometry, 1)
    dist = line.geometry.project(snapped, normalized=True)
    height = line['WS_BH_BOVENSTROOMS_L'] - dist * (line['WS_BH_BOVENSTROOMS_L']-line['WS_BH_BENEDENSTROOMS_L'])
    return height

if __name__ == '__main__':
    gdf_brug = read_featureserver(
        r'https://maps.brabantsedelta.nl/arcgis/rest/services/Extern/Kunstwerken/FeatureServer', 4)
    gdf_legger = read_featureserver(
        r'https://maps.brabantsedelta.nl/arcgis/rest/services/Extern/Legger_Vigerend/FeatureServer', 18)

    brug1 = gdf_brug.iloc[0]
    h1 = determine_bottom_height(brug1, gdf_legger)
    print(h1)
