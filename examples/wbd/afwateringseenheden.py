import geopandas as gpd
from pathlib import Path

# Inlezen input en klaarzetten output map
output_map = Path(r'c:\Users\908367\Box\BH8519 WBD DHYDRO\BH8519 WBD DHYDRO WIP\04_GIS\Lateralen')

exchange = Path(r'c:\Users\908367\Box\BH8519 WBD DHYDRO\BH8519 WBD DHYDRO WIP\00_Exchange\Waterschap Brabantse Delta')
afwat_gdf = gpd.read_file(exchange/'20211119_Afwateringseenheden'/'afwateringsgebieden_BrabantseDelta_02_11_2021_def.shp')
water_gdf = gpd.read_file(r'c:\Users\908367\Box\BH8519 WBD DHYDRO\BH8519 WBD DHYDRO WIP\04_GIS\kopie_server\Cat_A_Waterloop_Aa_of_Weerijs.shp')

# Selectie maken van de afwateringseenheden die overlappen met het netwerk van het projectgebied
water_poly = water_gdf.copy()
water_poly.geometry = water_gdf.buffer(0.1)
afwat = afwat_gdf[afwat_gdf.intersects(water_poly.unary_union)]
afwat.to_file(output_map/'selectie_afwateringseenheiden.gpkg', driver='GPKG')

# Per afwateringseenheid een nieuwe feature aanmaken:
# - Clip de waterlopen die binnen de afwaterignseenheid liggen
# - Kies het langste lijnsegment, plaats een punt 1 meter na het begin van dit segment,
# - Maak nieuwe feature aan met dit punt, met een naam, oppervlak en m3/s gebaseerd op afwaterignseenheid
laterals = gpd.GeoDataFrame()
for i, row in afwat.iterrows():
    clip_waterloop = gpd.clip(water_gdf, row.geometry)
    longest = clip_waterloop[clip_waterloop.length == clip_waterloop.length.max()]
    upstream = longest.iloc[0].geometry.interpolate(1)
    new_lat = gpd.GeoDataFrame(geometry=[upstream],
                               data={'ha': [row['oppervlakt']],
                                     'm3s': [row['oppervlakt'] / 1000],
                                     'ident': [f"Lat_{int(row['dtm2catID'])}"]},
                               index=[f"Lat_{int(row['dtm2catID'])}"])
    laterals = laterals.append(new_lat)

laterals.to_file(output_map/'laterals_aa_of_weerijs_MA.shp')