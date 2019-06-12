import argparse
import elasticsearch
import time
import datetime
from datetime import datetime, timedelta
import random

es = None

def set_es(url):
	global es
	es = elasticsearch.Elasticsearch(url)
	print elasticsearch.__version__

def check_index_existance(heartrate_index):
	ok = True
	if not es.indices.exists(heartrate_index):
		print heartrate_index,' has not been created, cannot simulate'
		ok = False
	return ok

def simulate_data(heartrate_index, range_from, range_to, date_from, date_to):
	print '=== SIMULATING HEARTRATE DATA ==='
	simulate_time = date_from;
	format = "%Y-%m-%dT%H:%M:%S.%f"
	id=0
	print id
	while(simulate_time < date_to):
		print id
		es.index(index=heartrate_index,id=id, body={ "id": '8704272056', "createdTime" : simulate_time.strftime(format), "heartrate": random.randint(range_from,range_to)})
		id = id+1
		simulate_time = simulate_time+timedelta(seconds=1)

def delete_data(heartrate_index, vulnerabilities_index):
	print '=== DELETING INDEX DATA ==='
	es.delete(index=heartrate_index, id=1)

def main():
	parser = argparse.ArgumentParser(description='Pushing simulate data to ES indexes', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('-url', dest='url', type=str, nargs='?', default='http://localhost:9207/', help='url to elasticsearch')
	#parser.add_argument('--delete', dest='delete',  action='store_true', default=False, help='delete mock entries')
	#parser.add_argument('--create_indexes', dest='create_indexes',  action='store_true', default=False, help='create indexes if they do not already exists')
	parser.add_argument('-hi', dest='heartrate_index', type=str, nargs='?', default='heartbeat', help='Name of heartbeat data index')


	args = parser.parse_args()
	format = "%Y-%m-%dT%H:%M:%S.%f"
	set_es(args.url)
	datetime_to = datetime.now()
	datetime_from = datetime_to - timedelta(seconds=2000)
	print datetime_from.strftime(format)
	print datetime_to.strftime(format)
	simulate_data('heartrate_index', 50, 120, datetime_from, datetime_to)
	#if not check_index_existance(args.address_index, vulnerabilities_index):
#		exit()

	#if args.delete:
#		delete_data(args.address_index, vulnerabilities_index)
	#else:
	#	populate_data(args.address_index, vulnerabilities_index)

	print 'Done'

if __name__ == '__main__':
  main()
