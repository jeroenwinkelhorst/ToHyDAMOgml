import shapely
import math
from shapely.geometry import LineString, Point
import logging
import geopandas as gpd
from tohydamogml.read_database import read_featureserver
import tqdm

def make_profile(gdf):
    new_points = gpd.GeoDataFrame(crs = 'EPSG:28992')
    for i, row in tqdm.tqdm(gdf.iterrows(), total=len(gdf)):
        up_line = _make_xyz(row, 'upstream')
        up_points = list(up_line.coords)
        for j in range(len(up_points)):
            new = gpd.GeoDataFrame(geometry=[Point(up_points[j])],
                                   data={'Code': [row['CODE']],
                                         'codeVolgnummer': [j + 1],
                                         'ProfielCode': [f'{row["CODE"]}_{j + 1}'],
                                         'TypeProfielCode': [4],
                                         'RuwheidsTypeCode': [4],
                                         'RuwheidsWaardeLaag': [30],
                                         'RuwheidsWaardeHoog': [20]})
            new_points = new_points.append(new)
        down_line = _make_xyz(row, 'downstream')
        down_points = list(down_line.coords)
        for j in range(len(up_points)):
            new = gpd.GeoDataFrame(geometry=[Point(down_points[j])],
                                   data={'Code': [f"{row['CODE']}_down"],
                                         'codeVolgnummer': [j + 1],
                                         'ProfielCode': [f'{row["CODE"]}_down_{j + 1}'],
                                         'TypeProfielCode': [4],
                                         'RuwheidsTypeCode': [4],
                                         'RuwheidsWaardeLaag': [30],
                                         'RuwheidsWaardeHoog': [20]})
            new_points = new_points.append(new)
    return new_points

def _make_xyz(row, up_or_down: str = 'upstream', profile_dist: float = 5, total_depth = 10):
    # Set up basic profile parameters: bottom width & total width based on talud
    bottom_width = row['WS_BODEMBREEDTE_L']
    if math.isnan(bottom_width):
        bottom_width = 2
        logging.info(f"Profielen maken: {row['CODE']} geen bodembreedte gevonden, bodembreedte op 2 gezet.")
    total_width = bottom_width + total_depth * row['WS_TALUD_LINKS_L'] + total_depth * row['WS_TALUD_RECHTS_L']
    if math.isnan(total_width):
        total_width = bottom_width + 2 * total_depth * 2
        logging.info(f"Profielen maken: {row['CODE']} geen taluds gevonden, talud op 2 gezet.")
    # Set up basic profile parameters: bottom level up or downstream. If either cannot be found, use the other, or 0
    if up_or_down.lower().startswith('up'):
        level_col = ['WS_BH_BOVENSTROOMS_L', 'WS_BH_BENEDENSTROOMS_L']
    else:
        level_col = ['WS_BH_BENEDENSTROOMS_L', 'WS_BH_BOVENSTROOMS_L']
    bottom_level = row[level_col[0]]
    if math.isnan(bottom_level):
        bottom_level = row[level_col[1]]
        if math.isnan(bottom_level):
            bottom_level = 0
            logging.info(f"Profielen maken: {row['CODE']} geen bodemhoogte gevonden, bodemhoogte op 0 gezet.")
        else:
            logging.info(f"Profielen maken: {row['CODE']} een van de bodemhoogtes niet gevonden, namelijk {level_col[0]}, "
                         f"bodemhoogte van {level_col[1]} gebruikt.")
    upper_level = bottom_level + total_depth

    # Profile will be created using a short sub-segment of the source-line-geometry.
    l = row['geometry'].length
    logging.info(f'Profielen maken: {up_or_down}, {row["CODE"]}, lengte: {l}, bodembreedte: {bottom_width}, '
                 f'bodemhoogte: {bottom_level}, totale diepte: {total_depth}')
    # If the total line is long enough, use a sub-segment that is 1 meter long,
    # otherwise make the segment on 1/5th and 2/5th of the total length of the line
    if l > (profile_dist * 2 + 1):
        dist1 = profile_dist
        dist2 = profile_dist - 1
    else:
        dist1 = l * 0.2
        dist2 = l * 0.4
    if up_or_down.lower().startswith('down'):
        dist1 = dist1 * -1
        dist2 = dist2 * -1

    point1 = row['geometry'].interpolate(dist1)
    point2 = row['geometry'].interpolate(dist2)
    baseline = LineString([point1, point2])

    left_inner = baseline.parallel_offset(bottom_width/2, 'left')
    right_inner = baseline.parallel_offset(bottom_width/2, 'right')
    left_inner_point = shapely.ops.transform(lambda x, y: (x, y, bottom_level), Point(left_inner.coords[0]))
    right_inner_point = shapely.ops.transform(lambda x, y: (x, y, bottom_level), Point(right_inner.coords[-1]))

    left_outer = baseline.parallel_offset(total_width/2, 'left')
    right_outer = baseline.parallel_offset(total_width/2, 'right')
    left_outer_point = shapely.ops.transform(lambda x, y: (x, y, upper_level), Point(left_outer.coords[0]))
    right_outer_point = shapely.ops.transform(lambda x, y: (x, y, upper_level), Point(right_outer.coords[-1]))

    profile_line = LineString([left_outer_point, left_inner_point, right_inner_point, right_outer_point])
    return profile_line

if __name__ == '__main__':
    # mask = r"c:\local\TKI_WBD\aanvullende_data\Aa_of_Weerijs_v2.shp"
    print(r'reading feature server...')
    gdf = read_featureserver(r"https://maps.brabantsedelta.nl/arcgis/rest/services/Extern/Legger_Vigerend/FeatureServer",
                             layer_index="18")
    print(r'feature server read!')
    # gdf = gpd.clip(gdf, mask)
    new_points = make_profile(gdf)
    new_points.to_file(r'output/dwarsprofiel/dwp_punten.gpkg', driver='GPKG')
    new_points.to_file(r'output/dwarsprofiel/dwp_punten.shp')