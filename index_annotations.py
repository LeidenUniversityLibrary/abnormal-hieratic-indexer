# Index annotations stored in a Simple Annotation Server in Elasticsearch
# © Leiden University Libraries, 2019
# See the LICENSE file for licensing information.


import requests
import json
from bs4 import BeautifulSoup, NavigableString
import logging, sys

ES_ENDPOINT = "http://localhost:9200"
SAS_ENDPOINT = "https://iiif.universiteitleiden.nl/anno/annotation"
OA_ANNOTATIONS_URI = SAS_ENDPOINT + "/"
SESSION = requests.Session()

ANNOTATED_BY = "dcterms:creator"
ANNOTATOR_NAME = "foaf:name"

LOGGER = logging.getLogger(__file__)
LOGGER.setLevel(logging.DEBUG)
LOG_HANDLER = logging.StreamHandler(sys.stdout)
LOG_HANDLER.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
LOGGER.addHandler(LOG_HANDLER)

manifest_labels = {}
canvas_labels = {}
canvas_images = {}
# Links from Canvas URIs to WordPress pages
canvas_pages = {}


def parse_manifest(uri: str):
    LOGGER.info("Parsing manifest {}".format(uri))
    manifest = SESSION.get(uri).json()
    manifest_labels[uri] = manifest["label"]
    for seq in manifest["sequences"]:
        for canvas in seq["canvases"]:
            canvas_labels[canvas["@id"]] = canvas["label"]
            canvas_images[canvas["@id"]] = {"base": canvas["images"][0]["resource"]["service"]["@id"],
                                            "h": canvas["images"][0]["resource"]["height"],
                                            "w": canvas["images"][0]["resource"]["width"],
                                            "h_ratio": canvas["height"] / canvas["images"][0]["resource"]["height"],
                                            "v_ratio": canvas["width"] / canvas["images"][0]["resource"]["width"]}
            for related in canvas.get("related"):
                if related["label"] == "Abnormal Hieratic Global Portal":
                    canvas_pages[canvas["@id"]] = related["@id"]


def get_manifest_label(uri: str):
    if uri not in manifest_labels:
        parse_manifest(uri)
    return manifest_labels[uri]


def find_annotations(canvas_filter=None):
    annotation_list = SESSION.get(OA_ANNOTATIONS_URI).json()
    if canvas_filter is None or canvas_filter == "":
        LOGGER.debug("Not filtering annotations")
        annotations = annotation_list["resources"]
    else:
        LOGGER.debug("Filtering annotations")
        annotations = [x for x in annotation_list["resources"] if canvas_filter in x["on"][0]["full"]]
    LOGGER.info("Found {} annotations".format(len(annotations)))
    return annotations


def svg_image(tag):
    """Return True when this is an SVG image"""
    return tag and tag.name == "img" and tag["src"].endswith(".svg")


def convert_annotation(annotation):
    """Converts an annotation to flat JSON object for Elasticsearch"""
    record = {}
    # Find annotation ID
    # 'https://iiif.universiteitleiden.nl/anno/annotation/1540300675536' => 1540300675536
    record["id"] = annotation["@id"].replace(OA_ANNOTATIONS_URI, "")
    chars = annotation["resource"][0]["chars"]
    soup = BeautifulSoup(chars, "html.parser")

    # Find SVG
    svg = soup.find_all(svg_image)
    if svg is not None:
        record["svg"] = [x["src"] for x in svg]

    # Find transliteration
    transliteration = soup.find("span",{"class": "transliteration"})
    if transliteration is not None:
        record["transliteration"] = transliteration.string

    # Find text type and translation
    for stripped_string in soup.stripped_strings:
        if stripped_string.startswith("Translation: "):
            record["translation"] = stripped_string.replace("Translation: ", "")
        elif stripped_string.startswith("Type: "):
            record["type"] = stripped_string.replace("Type: ", "")

    # Find annotator
    try:
        record["annotator"] = annotation[ANNOTATED_BY][ANNOTATOR_NAME]
    except KeyError:
        record["annotator"] = "Anonymous"

    # Find dates
    record["created"] = annotation["dcterms:created"]
    if "dcterms:modified" in annotation:
        record["modified"] = annotation["dcterms:modified"]

    # Find manifest, canvas with labels
    for target in annotation["on"]:
        if target["@type"] == "oa:SpecificResource" and "within" in target:
            if isinstance(target["within"], str):
                record["manifest"] = target["within"]
            else:
                record["manifest"] = target["within"]["@id"]
            record["manifest_label"] = get_manifest_label(record["manifest"])
            record["canvas"] = target["full"]
            record["canvas_label"] = canvas_labels[target["full"]]
            record["portal_url"] = canvas_pages[target["full"]]

            # Find coordinates; FIXME in case of non-choice
            record["xywh"] = target["selector"]["default"]["value"].replace("xywh=", "")
            record["x"], record["y"], record["w"], record["h"] = record["xywh"].split(",")

            # Find image URLs
            record["image_base_url"] = canvas_images[target["full"]]["base"]
            record["image_full_url"] = record["image_base_url"] + "/" + record["xywh"] + "/full/0/default.jpg"

    LOGGER.debug(json.dumps(record, indent=2))
    return record


def index_annotation_record(record):
    LOGGER.info("Updating %s", record["id"])

    res = SESSION.put(ES_ENDPOINT + "/annotations/anno/" + record["id"], json=record)
    LOGGER.info("Update returned status: %s", res.status_code)
    LOGGER.debug(res.json())
    res.raise_for_status()


def main():
    annos = find_annotations("https://iiif.universiteitleiden.nl/manifests/external/louvre/")
    for anno in annos:
        rec = convert_annotation(anno)
        index_annotation_record(rec)
    LOGGER.info("Done indexing")


if __name__ == "__main__":
    main()
