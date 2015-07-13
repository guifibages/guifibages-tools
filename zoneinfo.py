#!/usr/bin/env python
from __future__ import print_function

import argparse
import json
import logging
import os
import time

import requests
import libcnml


# http://stackoverflow.com/a/16695277
def DownloadFile(url, local_filename):
    logging.warning("Downloading %s to %s" % (url, local_filename))
    r = requests.get(url)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
    return


class ZoneInfo():
    def __init__(self, zone, cnml_cache="/tmp",
                 cnml_base="http://guifi.net/ca/guifi/cnml",
                 node_base="http://guifi.net/en/node",
                 output="json"):

        self.output = getattr(self, output)
        self.zone = zone
        self.node_base = cnml_base
        self.cnml_base = cnml_base
        self.cnml_cache = cnml_cache
        self.zone_id = self.get_zone_id()
        self.cnml = self.get_zone(self.zone_id)

    def get_zone_id(self):
        try:
            zone_id = int(self.zone)
        except ValueError:
            zones = self.get_zone(3671, "zones")
            result = sorted(filter(lambda z: self.zone in z.title.lower(),
                                   zones.getZones()), key=lambda z: z.id)
            zone_id = result[0].id
        return zone_id

    def get_zone(self, zone, kind="detail"):
        cnml_file = "{}/{}.{}.cnml".format(self.cnml_cache, zone, kind)
        cnml_url = "{}/{}/{}".format(self.cnml_base, zone, kind)
        try:
            age = time.time() - os.path.getmtime(cnml_file)
            if age > 24*3600:
                logging.warning("File age %s" % age)
                logging.warning("Too old, redownload")
                DownloadFile(cnml_url, cnml_file)
        except OSError:
            logging.warning("%s does not exist" % cnml_file)
            DownloadFile(cnml_url, cnml_file)
        return libcnml.CNMLParser(cnml_file)

    def json(self, r):
        print(json.dumps(r, indent=True))

    def list(self, kind):
        r = getattr(self, kind)()
        self.output(r)

    def zones(self):
        return [dict(id=z.id, title=z.title) for z in self.cnml.getZones()]

    def nodes(self):
        return [dict(id=n.id, title=n.title) for n in self.cnml.getNodes()]

    def st(self):
        return [dict(node=dict(title=st.parentNode.title, id=st.parentNode.id),
                     id=st.id, title=st.title)
                for st in filter(lambda n: len(n.radios) > 1,
                                 self.cnml.getDevices())]


def main():
    parser = argparse.ArgumentParser(
        description='Get information from Guifi Zones.')
    opt_list = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument('zone', nargs="?", default=3671,
                        help="Zone to work with")
    opt_list.add_argument('-z', dest='kind', action="store_const",
                          const='zones', default="zones",
                          help="List zones")
    opt_list.add_argument('-n', dest='kind', action="store_const",
                          const='nodes', default="zones",
                          help="List nodes")
    opt_list.add_argument('-m', dest='kind', action="store_const",
                          const='multi', default="zones",
                          help="List nodes with multiple links")
    opt_list.add_argument('-s', dest='kind', action="store_const",
                          const='st', default="zones",
                          help="List sts")

    args = parser.parse_args()
    zi = ZoneInfo(args.zone)
    zi.list(args.kind)

if __name__ == "__main__":
    main()
