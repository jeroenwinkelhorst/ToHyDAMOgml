import geopandas as gpd
from tohydamogml.read_database import read_featureserver
import shapely
from pathlib import Path

aangeleverd = Path(r'c:\Users\908367\Box\BH8519 WBD DHYDRO\BH8519 WBD DHYDRO WIP\00_Exchange\Waterschap Brabantse Delta')

gdf_afwat = gpd.read_file(aangeleverd/'20211119_Afwateringseenheden'/'afwateringsgebieden_BrabantseDelta_02_11_2021_def.shp')
gdf_mask = gpd.read_file(aangeleverd/'20210827_modelranden'/'RandenModelgebied.shp')
gdf_waterlopen = read_featureserver(r"https://maps.brabantsedelta.nl/arcgis/rest/services/Extern/Legger_Vigerend/FeatureServer", layer_index="18")
gdf_waterlopen.to_file('C:/local/wbd_legger.gpkg', driver='GPKG')

afwat = gdf_afwat[gdf_afwat.drop(columns='SHAPE').intersects(gdf_mask.unary_union)]
