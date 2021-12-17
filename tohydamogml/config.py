"""
CONFIG file voor HyDAMO_GML script
"""

DEFAULT_CRS = 'epsg:28992'

COLNAME_OID = "OBJECTID"

# GML config
XSD_PATH = r"src\xsd\nhiFeatureTypes.xsd"

XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"
NHI_NAMESPACE = "http://www.nhi.nu/gml"
GML_NAMESPACE = "http://www.opengis.net/gml"
XSD = "http://www.nhi.nu/gml nhiFeatureTypes.xsd"


RUWHEID_VEN_TE_CHOW = {
    'beton': 75,
    'gewapend beton': 75,
    'metselwerk': 65,
    'metaal': 80,
    'aluminium': 80,
    'ijzer': 80,
    'gietijzer': 75,
    'PVC': 80,
    'gegolfd plaatstaal': 65,
    'asbestcement': 110
}



