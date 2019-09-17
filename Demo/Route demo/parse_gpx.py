import argparse
import elasticsearch
import time
import datetime
from datetime import datetime, timedelta
import random
import xml.dom.minidom

es = None


def set_es(url):
    global es
    es = elasticsearch.Elasticsearch(url)
    print elasticsearch.__version__


def check_index_existance(route_index):
    ok = True
    if not es.indices.exists(route_index):
        print route_index, ' has not been created, cannot simulate'
        ok = False
    return ok


def simulate_data(route_index, dom_obj, date_from, inc):
    print '=== SIMULATING HEARTRATE DATA ==='
    simulate_time = date_from
    date_format = "%Y-%m-%dT%H:%M:%S.%f"
    doc_id = 0
    rtept = dom_obj.getElementsByTagName('rtept')
    for rte in rtept:
        lat = rte.getAttribute("lat")
        lon = rte.getAttribute("lon")
        print lat, lon
        name = rte.getElementsByTagName("name")[0]
        print name.firstChild.data
        es.index(index=route_index, id=doc_id,
                 body={"id": '8704272056', "createdTime": simulate_time.strftime(date_format),
                       "name": name.firstChild.data,
                       "Position": {"lat": lat, "lon": lon}})
        doc_id += 1
        simulate_time += timedelta(seconds=inc)


def delete_data(route_index):
    print '=== DELETING INDEX DATA ==='
    es.delete(index=route_index, id=1)


def main():
    parser = argparse.ArgumentParser(description='Pushing simulate data to ES indexes',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-url', dest='url', type=str, nargs='?', default='http://localhost:9207/',
                        help='url to elasticsearch')
    # parser.add_argument('--delete', dest='delete',  action='store_true', default=False, help='delete mock entries')
    # parser.add_argument('--create_indexes', dest='create_indexes',  action='store_true', default=False, help='create
    # indexes if they do not already exists')

    parser.add_argument('-i', dest='route_index', type=str, nargs='?', default='route_index',
                        help='Name of route index data index')

    args = parser.parse_args()
    set_es(args.url)

    dom_obj = xml.dom.minidom.parse("route.gpx")
    simulate_data(args.route_index, dom_obj, datetime.now(), 3)
    # if not check_index_existance(args.route_index):
    # exit()

    if args.delete:
        delete_data(args.route_index)
    else:
        simulate_data(args.route_index, dom, datetime.now(), 3)

    print 'Done'


if __name__ == '__main__':
    main()
