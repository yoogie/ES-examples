import argparse
from elasticsearch import Elasticsearch as ES7, helpers, client
from elasticsearch5 import Elasticsearch as ES5

multi_types = 'multi_types'
type_person = 'type_person'
type_building = 'type_building'
migrate_pipeline = 'migrate_pipeline'

pipeline_json = {
"description": "Pipeline for splitting data by type",
"processors": [{ "set": { "field": "_index", "value": "type_{{type}}"}},{ "remove": { "field": "type"}}]
}

def populate_pipeline(es7):
	client.IngestClient(es7).put_pipeline(id = migrate_pipeline, body = pipeline_json)

def reindex_data(es5, es7):
	print '=== REINDEX multi_types data using pipeline ==='
	scroll_size = 1000
	page = es5.search(index = multi_types, scroll = '1m', size = scroll_size, body = {"sort": ["_doc"], "query": {"match_all": {}}})
	page_size = len(page['hits']['hits'])
	while (page_size > 0):
		sid = page['_scroll_id']
		bulk = []
		for doc in page['hits']['hits']:
			doc['_source']['type'] = doc['_type'] #Add type as field instead
			bulk_str = { '_index': 'x', 'pipeline': migrate_pipeline, '_id': doc['_id'], '_source': doc['_source']}
			bulk.append(bulk_str)

		ok, failed = helpers.bulk(es7, bulk)
		if len(failed) > 0:
			print 'Failed to bulk documents to es7 cluster'
			return False
		page = es5.scroll(scroll_id = sid, scroll = '1m')
		page_size = len(page['hits']['hits'])
	return True

def populate_multitype_data(es5):
	print '=== POPULATING multi_types data ==='
	es5.index(index=multi_types, id=1, doc_type ='person', body={"Name": "Bob","age":20})
	es5.index(index=multi_types, id=2, doc_type ='building', body={"Floors": 2,"Doors":4})
	es5.index(index=multi_types, id=3, doc_type ='person', body={"Name": "Alice","age":31})
	es5.index(index=multi_types, id=4, doc_type ='building', body={"Floors": 5,"Doors":41})
	es5.indices.flush(index=multi_types)

def cleanup(es5, es7):
	print '=== DELETING INDEX multi_types in ES5 cluster ==='
	es5.indices.delete(index=multi_types, ignore=[404])

	print '=== DELETING INDEX type_person in ES7 cluster ==='
	es7.indices.delete(index=type_person, ignore=[404])

	print '=== DELETING INDEX type_building in ES7 cluster ==='
	es7.indices.delete(index=type_building, ignore=[404])
	
	print '=== DELETING migration pipeline in ES7 cluster ==='
	client.IngestClient(es7).delete_pipeline(id=migrate_pipeline, ignore=[404])

def main():
	parser = argparse.ArgumentParser(description='Indexing multiptype data into ES5 cluster and reindex to ES7 using pipeline', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('-es5', dest='es5_url', type=str, nargs='?', default='http://localhost:9200/', help='url to es 5 cluster')
	parser.add_argument('-es7', dest='es7_url', type=str, nargs='?', default='http://localhost:9207/', help='url to es 7 cluster')
	parser.add_argument('--cleanup', dest='cleanup',  action='store_true', default=False, help='Delete indices and pipeline created by this script')
	args = parser.parse_args()

	es5 = ES5(args.es5_url)
	es7 = ES7(args.es7_url)

	if args.cleanup:
		cleanup(es5, es7)
		exit()
	
	populate_multitype_data(es5)
	populate_pipeline(es7)
	reindex_data(es5, es7)

if __name__ == '__main__':
	main()
