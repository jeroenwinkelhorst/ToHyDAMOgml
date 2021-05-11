from arcgis.features import FeatureLayerCollection
import geopandas as gpd

url = r'https://maps.brabantsedelta.nl/arcgis/rest/services/Extern/Kunstwerken/FeatureServer'
feature = FeatureLayerCollection(url)
feature_layer = feature.layers[8]
query_result1 = feature_layer.query(where='OBJECTID>=0')
geojson = query_result1.to_geojson
gdf = gpd.read_file(geojson)
feature.head()