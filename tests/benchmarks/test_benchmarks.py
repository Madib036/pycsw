# =================================================================
#
# Performance benchmarks for pycsw
#
# These benchmarks cover the core utility functions that are on the
# hot path of request processing: XPath evaluation, geometry
# conversions, link parsing, URL handling, and XML text extraction.
#
# =================================================================

import json

import pytest

from pycsw.core import util


# -- XPath / namespace evaluation ------------------------------------------

NSMAP = {
    "csw": "http://www.opengis.net/cat/csw/2.0.2",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dct": "http://purl.org/dc/terms/",
    "ows": "http://www.opengis.net/ows",
    "gmd": "http://www.isotc211.org/2005/gmd",
}


def test_nspath_eval_simple(benchmark):
    """Benchmark simple namespace XPath resolution."""
    benchmark(util.nspath_eval, "csw:Record", NSMAP)


def test_nspath_eval_nested(benchmark):
    """Benchmark deeply nested XPath resolution."""
    benchmark(
        util.nspath_eval,
        "csw:GetRecordsResponse/csw:SearchResults/csw:Record",
        NSMAP,
    )


# -- Geometry conversions --------------------------------------------------

def test_bbox2wktpolygon(benchmark):
    """Benchmark bounding box to WKT polygon conversion."""
    benchmark(util.bbox2wktpolygon, "-180.0, -90.0, 180.0, 90.0")


def test_wkt2geom_point(benchmark):
    """Benchmark WKT point parsing to bounds."""
    benchmark(util.wkt2geom, "POINT (10 10)", bounds=True)


def test_wkt2geom_polygon(benchmark):
    """Benchmark WKT polygon parsing to bounds."""
    wkt = (
        "POLYGON((-180.00 -90.00, -180.00 90.00, "
        "180.00 90.00, 180.00 -90.00, -180.00 -90.00))"
    )
    benchmark(util.wkt2geom, wkt, bounds=True)


def test_wkt2geom_ewkt(benchmark):
    """Benchmark Extended WKT (SRID prefix) parsing."""
    benchmark(util.wkt2geom, "SRID=4326;POINT (10 10)", bounds=True)


def test_geojson_geometry2bbox(benchmark):
    """Benchmark GeoJSON polygon to bbox conversion."""
    geometry = {
        "type": "Polygon",
        "coordinates": [[
            [100.0, 0.0],
            [101.0, 0.0],
            [101.0, 1.0],
            [100.0, 1.0],
            [100.0, 0.0],
        ]],
    }
    benchmark(util.geojson_geometry2bbox, geometry)


def test_wktenvelope2bbox(benchmark):
    """Benchmark WKT ENVELOPE to bbox string conversion."""
    benchmark(util.wktenvelope2bbox, "ENVELOPE (-180,180,90,-90)")


# -- Link / JSON parsing ---------------------------------------------------

CSV_LINKS = (
    "roads,my roads,OGC:WMS,http://example.org/wms^"
    "roads,my roads,OGC:WFS,http://example.org/wfs"
)

JSON_LINKS = json.dumps([
    {
        "name": "roads",
        "description": "my roads",
        "protocol": "OGC:WMS",
        "url": "http://example.org/wms",
    },
    {
        "name": "roads",
        "description": "my roads",
        "protocol": "OGC:WFS",
        "url": "http://example.org/wfs",
    },
])


def test_jsonify_links_csv(benchmark):
    """Benchmark legacy CSV link parsing."""
    benchmark(util.jsonify_links, CSV_LINKS)


def test_jsonify_links_json(benchmark):
    """Benchmark JSON link parsing."""
    benchmark(util.jsonify_links, JSON_LINKS)


# -- URL handling -----------------------------------------------------------

def test_bind_url_no_query(benchmark):
    """Benchmark URL binding with no existing query string."""
    benchmark(util.bind_url, "http://host/wms")


def test_bind_url_with_query(benchmark):
    """Benchmark URL binding with an existing query string."""
    benchmark(util.bind_url, "http://host/wms?foo=bar")


# -- IP / network utilities -------------------------------------------------

def test_ip_in_network_cidr(benchmark):
    """Benchmark CIDR network membership check."""
    benchmark(util.ip_in_network_cidr, "192.168.100.14", "192.168.0.0/16")


def test_ipaddress_in_whitelist(benchmark):
    """Benchmark IP whitelist lookup with mixed rules."""
    whitelist = [
        "10.0.0.1",
        "172.16.0.0/12",
        "192.168.100.*",
        "192.168.0.0/16",
    ]
    benchmark(util.ipaddress_in_whitelist, "192.168.100.14", whitelist)


# -- Text extraction --------------------------------------------------------

SAMPLE_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<csw:Record xmlns:csw="http://www.opengis.net/cat/csw/2.0.2"
            xmlns:dc="http://purl.org/dc/elements/1.1/"
            xmlns:dct="http://purl.org/dc/terms/">
    <dc:identifier>abc-123</dc:identifier>
    <dc:title>National Elevation Dataset</dc:title>
    <dc:subject>Elevation</dc:subject>
    <dc:subject>Hypsography</dc:subject>
    <dct:abstract>High-resolution elevation data for the United States.</dct:abstract>
    <dc:type>dataset</dc:type>
    <dc:format>GeoTIFF</dc:format>
</csw:Record>
"""


def test_get_anytext_xml(benchmark):
    """Benchmark free-text bag extraction from an XML string."""
    benchmark(util.get_anytext, SAMPLE_XML)


def test_get_anytext_list(benchmark):
    """Benchmark free-text bag extraction from a word list."""
    words = [
        "elevation", "hypsography", "contours", "DEM",
        "terrain", "topography", "USGS", "raster",
    ]
    benchmark(util.get_anytext, words)


# -- Miscellaneous helpers --------------------------------------------------

def test_datetime2iso8601(benchmark):
    """Benchmark datetime to ISO 8601 conversion."""
    import datetime
    value = datetime.datetime(2024, 6, 15, 12, 30, 45)
    benchmark(util.datetime2iso8601, value)


def test_get_version_integer(benchmark):
    """Benchmark OGC version string to integer conversion."""
    benchmark(util.get_version_integer, "2.0.2")


def test_secure_filename(benchmark):
    """Benchmark secure filename sanitization."""
    benchmark(util.secure_filename, "../../../etc/passwd")
