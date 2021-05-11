import fiona

# url = r"ESRIJSON:/https://maps.brabantsedelta.nl/arcgis/rest/services/Extern/Kunstwerken/FeatureServer"
#
# with fiona.open(url, driver='ESRIJSON') as collection:
#     features = list(collection)


url2 = r"https://maps.brabantsedelta.nl/arcgis/rest/services/Extern/Kunstwerken/FeatureServer"
with fiona.open(url2) as collection:
    features = list(collection)