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


def check_index_existance(index):
    ok = True
    if not es.indices.exists(index):
        print index, ' has not been created'
        ok = False
    return ok


def setup_index(synonym_index):
    request_body = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "index": {
                "analysis": {
                    "analyzer": {
                        "synonym": {
                            "tokenizer": "standard",
                            "filter": ["synonym"]
                        }
                    },
                    "filter": {
                        "synonym": {
                            "type": "synonym",
                            "synonyms": [
                                "foo, bar => baz",
                                "laptop, notebook",
                                "ipod, i-pod, i pod => ipod",
                                "universe, cosmos"]
                        }
                    }
                }
            }
        },
        "mappings": {
                "properties": {
                    "test": {"type": "text", "analyzer": "synonym"}
                }}
    }
    es.indices.create(index=synonym_index, body=request_body)


def setup_data(synonym_index):
    es.index(index=synonym_index, id=1, body={"test": "bar"})
    es.index(index=synonym_index, id=2, body={"test": "foo"})
    es.index(index=synonym_index, id=3, body={"test": "baz"})

def delete_data(synonym_index):
    print '=== DELETING INDEX DATA ==='
    es.delete(index=synonym_index, id=1)


def main():
    parser = argparse.ArgumentParser(description='Pushing data to ES indexes',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-url', dest='url', type=str, nargs='?', default='http://localhost:9200/',
                        help='url to elasticsearch')
    parser.add_argument('--delete', dest='delete',  action='store_true', default=False, help='delete index')
    # parser.add_argument('--create_indexes', dest='create_indexes',  action='store_true', default=False, help='create
    # indexes if they do not already exists')
    parser.add_argument('-hi', dest='synonym_index', type=str, nargs='?', default='test_synonym',
                        help='Name of data index')

    args = parser.parse_args()
    set_es(args.url)

    if args.delete:
        delete_data(args.synonym_index)
    else:
        setup_index(args.synonym_index)

    if check_index_existance(args.synonym_index):
        setup_data(args.synonym_index)

    print 'Done'


if __name__ == '__main__':
    main()
