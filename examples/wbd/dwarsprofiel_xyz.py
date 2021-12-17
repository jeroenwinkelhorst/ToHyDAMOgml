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
        length = row.geometry.length
        if length > 20:
            up_dist_main, up_dist_help = 5, 10
            down_dist_main, down_dist_help = length-5, length-10
        else:
            up_dist_main, up_dist_help = length*0.25, length*0.5
            down_dist_main, down_dist_help = length*0.75, length*0.5
        up_line = _make_xyz(row=row, distance_main=up_dist_main, distance_help=up_dist_help,
                            bottom_level=row['WS_BH_BOVENSTROOMS_L'], bottom_width=row['WS_BODEMBREEDTE_L'],
                            talud_l=row['WS_TALUD_LINKS_L'], talud_r=row['WS_TALUD_RECHTS_L'], total_depth = 10)
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
        down_line = _make_xyz(row=row, distance_main=down_dist_main, distance_help=down_dist_help,
                              bottom_level=row['WS_BH_BENEDENSTROOMS_L'], bottom_width=row['WS_BODEMBREEDTE_L'],
                              talud_l=row['WS_TALUD_LINKS_L'], talud_r=row['WS_TALUD_RECHTS_L'], total_depth = 10)
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

def _make_xyz(row, distance_main, distance_help, bottom_level, bottom_width, talud_l, talud_r, total_depth = 10):
    # Set up basic profile parameters: bottom width & total width based on talud
    if math.isnan(bottom_width):
        bottom_width = 2
        logging.info(f"Profielen maken: {row['CODE']} geen bodembreedte gevonden, bodembreedte op 2 gezet.")
    total_width = bottom_width + total_depth * talud_l + total_depth * talud_r
    if math.isnan(total_width):
        total_width = bottom_width + 2 * total_depth * 2
        logging.info(f"Profielen maken: {row['CODE']} geen taluds gevonden, talud op 2 gezet.")

    upper_level = bottom_level + total_depth

    # Profile will be created using a short sub-segment of the source-line-geometry.
    l = row['geometry'].length
    logging.info(f'Profielen maken: {row["CODE"]}, op afstand: {distance_main} van lengte: {l}, '
                 f'bodembreedte: {bottom_width}, '
                 f'bodemhoogte: {bottom_level}, totale diepte: {total_depth}')

    point1 = row['geometry'].interpolate(distance_main)
    point2 = row['geometry'].interpolate(distance_help)
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
    mask = gpd.read_file(r"c:\local\TKI_WBD\aanvullende_data\Aa_of_Weerijs_v2.shp")
    print(r'reading feature server...')
    gdf = read_featureserver(r"https://maps.brabantsedelta.nl/arcgis/rest/services/Extern/Legger_Vigerend/FeatureServer",
                             layer_index="18")
    gdf = gdf[gdf.drop(columns='SHAPE').intersects(mask.unary_union)]

    print(r'feature server read!')
    # gdf = gpd.clip(gdf, mask)
    new_points = make_profile(gdf)
    new_points.to_file(r'output/dwarsprofiel/dwp_punten_2.gpkg', driver='GPKG')
    new_points.to_file(r'output/dwarsprofiel/dwp_punten_2.shp')