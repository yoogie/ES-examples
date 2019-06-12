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
		print route_index,' has not been created, cannot simulate'
		ok = False
	return ok

def simulate_data(route_index, dom, date_from, inc):
	print '=== SIMULATING HEARTRATE DATA ==='
	simulate_time = date_from;
	format = "%Y-%m-%dT%H:%M:%S.%f"
	id=0
	rtept=dom.getElementsByTagName('rtept')
	for rte in rtept:
		lat = rte.getAttribute("lat")
		lon = rte.getAttribute("lon")
		print lat, lon
		name = rte.getElementsByTagName("name")[0]
		print name.firstChild.data
		es.index(index=route_index,id=id, body={ "id": '8704272056', "createdTime" : simulate_time.strftime(format), "name": name.firstChild.data, "Position":{"lat" : lat,"lon" : lon}})
		id = id+1
		simulate_time = simulate_time+timedelta(seconds=inc)
	

def delete_data(route_index, vulnerabilities_index):
	print '=== DELETING INDEX DATA ==='
	es.delete(index=route_index, id=1)

def main():
	parser = argparse.ArgumentParser(description='Pushing simulate data to ES indexes', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('-url', dest='url', type=str, nargs='?', default='http://localhost:9207/', help='url to elasticsearch')
	#parser.add_argument('--delete', dest='delete',  action='store_true', default=False, help='delete mock entries')
	#parser.add_argument('--create_indexes', dest='create_indexes',  action='store_true', default=False, help='create indexes if they do not already exists')
	parser.add_argument('-hi', dest='route_index', type=str, nargs='?', default='route_index', help='Name of heartbeat data index')


	args = parser.parse_args()
	format = "%Y-%m-%dT%H:%M:%S.%f"
	set_es(args.url)

	dom = xml.dom.minidom.parse("route.gpx")
	simulate_data('route_index', dom,datetime.now(), 3)
	#if not check_index_existance(args.address_index, vulnerabilities_index):
#		exit()

	#if args.delete:
#		delete_data(args.address_index, vulnerabilities_index)
	#else:
	#	populate_data(args.address_index, vulnerabilities_index)

	print 'Done'

if __name__ == '__main__':
  main()
