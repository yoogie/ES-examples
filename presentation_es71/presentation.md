# Some of the changes in ES 7
## Disable refresh on searche idle shards
The refresh rate states how often new documents in the index are searchable. If a shard has not been queried for a while the refresh setting is set to -1, 
i.e turned off, by default. This impacts the index rate of a shard/index that is not searched that often. Ex, when poulating a new index with data, before switching it "live" using an alias or such.

## No more multi type indices
It is no longer allowed to have documents of different type in the same index. In earlier versions of ES it has been possible to store different documenttypes in the same index. Which has sometimes missleda the user that it is possible to have different datamodels in the same index. It has however been a disception. Even in earlier version two documents in the same index has "shared mapping", meaning that if the document have had fields with the same name the same mapping has applied. 

One way to handle is to reindex into one index per type:
<code>_reindex 
{
  "source": {
    "index": "products",
    "type": "one-type"
  },
  "dest": {
    "index": "one-type-index"
  }
}</code>

An other is to use some field and a ingest pipeline to do the same thing:

* Example: Reindex using pipeline

## Default geo_shape is now vector based
Geo shapes are now stored as vector data.
* Example?

## Discovery configuration changes
* Show new settings vs old, how to "split" cluster.

## Default number of shards 5->1 but also number_of_routing_shards is now set
Previous versions had default 5 shards per index. This is now lowered to 1. However in order to cope with the risk of this beeing to low the number_of_routing_shards has been set default to allow spliting of a factor 2 all the way to 1024.
Unfortunantly there is no easy way to see the number_of_routing_shards setting to verify if it is the default or not. A workaround is to call the _split api with an invalid number of shards and read the error message.
Ex:

```
POST my_index/_split/my_index2
{
  "settings": {
    "index.number_of_shards": 1300
  }
}
```

Error response from ES: 
```
{
  "error": {
    "root_cause": [
      {
        "type": "illegal_argument_exception",
        "reason": "Failed to parse value [1300] for setting [index.number_of_shards] must be <= 1024"
      }
    ],
    "type": "illegal_argument_exception",
    "reason": "Failed to parse value [1300] for setting [index.number_of_shards] must be <= 1024"
  },
  "status": 400
}
```


## Adaptive replica selection default true
Earlier only round robbin, late 6.x version added adaptive replica (ARS) selection as an option. Meaning that the coordinating nodes keep track of how long a query for a shard takes at each node and chooses the node that is most likely to be done fastest with the query.

https://www.elastic.co/blog/improving-response-latency-in-elasticsearch-with-adaptive-replica-selection

## hits.total is now an object
One of the changes done is that hits.total in the response is now an object. This affects client implementations and users thereof. Might be note worthy for scripts implementing "scoll" or such.

# Sizing a cluster
The default answere to any question regarding cluster performance or scaling is "it depends". And it realy does. Scaling the cluster or the performance if a cluster follows the same theory as any optimization does. Meassure, alter, meassure alter. 
As always it is best to use live data or data and lad that is as realistic as possible. The index performance and the query performance ar two different things and requirements regarding how long before data

# Deprecation log
* Example: Use deprecated functions, see log, fix it

# Slow query log
* Example: Enable log with different tresholds, trigger by using slow query. Advanced agg?

# Reindex
## Reindex to change mapping
How to keep track of reindex operations?
* Example: Using field to keep track

## Throtteling reindex job
* Example: Show how to find job and tweek throtteling in advance
Start of with 1s and higher to make it visible

# Data life cycle

## Rollup

## Index migration (hot/warm)

# Cross cluser?

# Ingestpipelines
The elastic stack is moving in the direction of having beats as data shippers. Going in that direction makes the logstash less key for many cases. The second area for logstash being the data mangling, looking into ingestpipelines and dedicated ingest nodes is now more interesting. More and more functionality is added into processors in the pipelines. Even though logstash is still very much needed when it comes to advanced stuff or when multiple outputs are needed, there is now quite a few cases that is completly managele within ES it self.

## Grok
Very similar to regular expressions. There is a list of defined patterns: 
http://grokdebug.herokuapp.com/patterns# and it is possible to provide own pattern definitios that can then be reused. 

Ex:
```
POST _ingest/pipeline/_simulate
{
  "pipeline": {
    "description": "Grok example",
    "processors": [
      {
        "grok": {
          "field": "message",
          "patterns": [
            "%{TS:tstamp}%{SPACE}%{PROC:proc}%{SPACE}%{WORD:severity}:%{SPACE}%{GREEDYDATA:msg}"
          ],
          "pattern_definitions": {
            "TS": "%{YEAR}::%{MONTHNUM}::%{MONTHDAY} at %{HOUR}.%{MINUTE}.%{SECOND}",
            "PROC": "([a-zA-Z0-9._-]+)"
          }
        }
      }
    ]
  },
  "docs": [
    {
      "_source": {
        "message": "2018::03::12 at 10.03.01    my1_Proc Verbose:This is some text"
      }
    }
  ]
}
```

Result:
```
{
  "docs" : [
    {
      "doc" : {
        "_index" : "_index",
        "_type" : "_doc",
        "_id" : "_id",
        "_source" : {
          "severity" : "Verbose",
          "msg" : "This is some text",
          "proc" : "my1_Proc",
          "tstamp" : "2018::03::12 at 10.03.01",
          "message" : "2018::03::12 at 10.03.01    my1_Proc Verbose:This is some text"
        },
        "_ingest" : {
          "timestamp" : "2019-05-28T11:38:34.126Z"
        }
      }
    }
  ]
}
```

## Kv
A common data structure is the "key-value". It is therefor no supprise that there exists a processor that can be used to dynamicly handle key-value formated data.

Ex extracting some sensore values from a string containing both text and data. First processor is grok-ing out the data part of the string, second processor uses the built in key-value parser to extract sensor data and the last processor gets rid of the temporary field created by the grok processor before indexing the document:
```
POST _ingest/pipeline/_simulate
{
  "pipeline": {
    "description": "KV example",
    "processors": [
      {
        "grok": {
          "field": "message",
          "patterns": [
            "These are the values: %{GREEDYDATA:sensor_data}"
          ]
        }
      },
      {
        "kv": {
          "field": "sensor_data",
          "field_split": ";",
          "value_split": ":"
        }
      },
      {
        "remove": {
          "field": "sensor_data"
        }
      }
    ]
  },
  "docs": [
    {
      "_source": {
        "message": "These are the values: sensor1:101.2;sensor2:100.0;sensor3:0.0"
      }
    }
  ]
}
```

Result:
```
{
  "docs" : [
    {
      "doc" : {
        "_index" : "_index",
        "_type" : "_doc",
        "_id" : "_id",
        "_source" : {
          "sensor2" : "100.0",
          "sensor3" : "0.0",
          "message" : "These are the values: sensor1:101.2;sensor2:100.0;sensor3:0.0",
          "sensor1" : "101.2"
        },
        "_ingest" : {
          "timestamp" : "2019-05-29T10:45:33.595Z"
        }
      }
    }
  ]
}
```
## Json
An other common data structure is "json". All documents within ES being json It is even less of a surprise to see that the json processor in the list of available processors when creating a pipeline.

Ex parsing a line from the elasticsearch deprecation.json log:
```
POST _ingest/pipeline/_simulate
{
  "pipeline": {
    "description": "JSON example",
    "processors": [
      {
        "json": {
          "field": "message"
        }
      }
    ]
  },
  "docs": [
    {
      "_source": {
        "message": """{"type": "deprecation", "timestamp": "2019-05-28T13:06:51,315+0200", "level": "WARN", "component": "o.e.d.a.i.SimulatePipelineRequest", "cluster.name": "dev-71", "node.name": "bjorn", "cluster.uuid": "zhT6bk8aTjWTALXw_K9r7Q", "node.id": "6yZXJFXsT76AL9jA28dcHw",  "message": "[types removal] specifying _type in pipeline simulation requests is deprecated"  } """
      }
    }
    ]
}
```

Result:
```
{
  "docs" : [
    {
      "doc" : {
        "_index" : "_index",
        "_type" : "_doc",
        "_id" : "_id",
        "_source" : {
          "message" : {
            "node.id" : "6yZXJFXsT76AL9jA28dcHw",
            "cluster.name" : "dev-71",
            "component" : "o.e.d.a.i.SimulatePipelineRequest",
            "level" : "WARN",
            "node.name" : "bjorn",
            "type" : "deprecation",
            "message" : "[types removal] specifying _type in pipeline simulation requests is deprecated",
            "cluster.uuid" : "zhT6bk8aTjWTALXw_K9r7Q",
            "timestamp" : "2019-05-28T13:06:51,315+0200"
          }
        },
        "_ingest" : {
          "timestamp" : "2019-05-29T10:33:22.057Z"
        }
      }
    }
  ]
}
```

## Drop
One of the latest aditions of processors available is the drop processor. It makes it possible to do some data processing and then take the desicion that the data is not interesting and drop it.

Ex dropping all documents by a user 'Spam-bot'. In the simulate API it is not easy to see that the document gets droped, therefore this example is done against real pipeline/index instead of using the simualate PIA
```
PUT _ingest/pipeline/dropper
{
    "description": "Drop example",
    "processors": [
      {
        "drop": {
          "if": "ctx.user_name == 'Spambot'"
        }
      }
    ]
}

POST slask/_create/1?pipeline=dropper
{
  "message": "Interesting stuff",
  "user_name": "Bob"
}

PUT slask/_create/2?pipeline=dropper
{
  "message": "Useless spam from a bot",
  "user_name": "Spambot"
}

POST slask/_search
```


Result:
```
{
  "_index" : "slask",
  "_type" : "_doc",
  "_id" : "1",
  "_version" : 1,
  "result" : "created",
  "_shards" : {
    "total" : 2,
    "successful" : 1,
    "failed" : 0
  },
  "_seq_no" : 0,
  "_primary_term" : 1
}

{
  "_index" : "slask",
  "_type" : "_doc",
  "_id" : "2",
  "_version" : -4,
  "result" : "noop",
  "_shards" : {
    "total" : 0,
    "successful" : 0,
    "failed" : 0
  }
}

{
  "took" : 0,
  "timed_out" : false,
  "_shards" : {
    "total" : 1,
    "successful" : 1,
    "skipped" : 0,
    "failed" : 0
  },
  "hits" : {
    "total" : {
      "value" : 1,
      "relation" : "eq"
    },
    "max_score" : 1.0,
    "hits" : [
      {
        "_index" : "slask",
        "_type" : "_doc",
        "_id" : "1",
        "_score" : 1.0,
        "_source" : {
          "user_name" : "Bob",
          "message" : "Interesting stuff"
        }
      }
    ]
  }
}

```
DELETE _ingest/pipeline/dropper
DELETE slask

## split 
The split processor can be used to split a field into a list of values. A useful example is when data is passed in a string but the data is more useful as a list of keywords.
Ex parsing the localities of a document and store it as a list of keywords:
```
POST _ingest/pipeline/_simulate
{
  "pipeline": {
    "description": "Split locale text into keyword list",
    "processors": [
      {
        "split": {
          "field": "locales",
          "separator": ","
        }
      }
    ]
  },
  "docs": [
    {
      "_source": {
        "locales": "en-uk,en-us"
      }
    },
    {
      "_source": {
        "locales": "sv-se"
      }
    }
    ]
}
```

Result:
```
{
  "docs" : [
    {
      "doc" : {
        "_index" : "_index",
        "_type" : "_doc",
        "_id" : "_id",
        "_source" : {
          "locales" : [
            "en-uk",
            "en-us"
          ]
        },
        "_ingest" : {
          "timestamp" : "2019-06-11T19:30:38.9647143Z"
        }
      }
    },
    {
      "doc" : {
        "_index" : "_index",
        "_type" : "_doc",
        "_id" : "_id",
        "_source" : {
          "locales" : [
            "sv-se"
          ]
        },
        "_ingest" : {
          "timestamp" : "2019-06-11T19:30:38.9647143Z"
        }
      }
    }
  ]
}
```

## script
If there is no generic processor that fits your need, there is always the script processor.
Ex calculating the lenght of a field and storing it as a new field:
```
POST _ingest/pipeline/_simulate
{
  "pipeline": {
    "description": "Store message lenght as a field",
    "processors": [
      {
        "script": {
          "source": """
          if(ctx.containsKey("message")) {
            ctx.message_len = ctx.message.length();
          }
          else {
            ctx.message_len = 0;
          }
          """
        }
      }
    ]
  },
  "docs": [
    {
      "_source": {
        "message": "This is my story"
      }
    },
    {
      "_source": {
        "message": ""
      }
    }
    ]
}
```

Result:
```
{
  "docs" : [
    {
      "doc" : {
        "_index" : "_index",
        "_type" : "_doc",
        "_id" : "_id",
        "_source" : {
          "message" : "This is my story",
          "message_len" : 16
        },
        "_ingest" : {
          "timestamp" : "2019-06-11T19:32:35.4231577Z"
        }
      }
    },
    {
      "doc" : {
        "_index" : "_index",
        "_type" : "_doc",
        "_id" : "_id",
        "_source" : {
          "message" : "",
          "message_len" : 0
        },
        "_ingest" : {
          "timestamp" : "2019-06-11T19:32:35.4231577Z"
        }
      }
    }
  ]
}
```

## pipeline - pipeline
Since there has been a lot of work done in the ingest pipeline world, a logical edition is also the pipeline processor. It makes it possible to reuse pipelines. I.e apply the same pice of logic into multiple workflows. Something to notice here though is that only the final result of all processing is what will enter the elasticsearch database. 
We had a missunderstanding when this processor was first relesed and tried to reuse some logic that dropped a document in one pipeline and would index it in an other. However, if droped in one it is droped in all.


# ECS
Elastic common schema has been implemented across large parts of the Elastic Stack. Since beats 7.0 all beats and beat modules genereate ECS format events by default.
The ECS provides common naming conventions for fields and sets or nested fields. Examples for a set is the host parameters, host.ip, host.hostname etc. The strive here is to exclude redundant naming, hostname being an exception.
The ECS has turned the default mapping around, instead of doing the default my_filed as text annd my_field.keyword for keyword the ECS has my_field as keyword and my_field.text for text only for where free text search is needed. There are exceptions to this rule aswell, the fileds message and error.message are only indexed as text for free text search, due to legacy reasons stretching all the old beats.


# Cross index annotaion
One nice feature of Kibana vizualisations is to add anotations between indices. Ex plotting the overall cpu usage in a timelion graph and annotate critical errors from an application logfile. Or as in the LoginOverCPU exampel vizualisation where the successfull logon events from the windows eventlog is annotated over the normalized cpu usage from metricbeat.

Settings added in metricbeat.xml to enable monitoring of windows services and to get cpu in normalized values
<code>
metricbeat.modules:
- module: windows
  metricsets: ["service"]
  period: 60s
 
 
 - module: system
  cpu.metrics: [percentages, normalized_percentages]
</code>

# Performance
## Top k hits
https://www.elastic.co/blog/faster-retrieval-of-top-hits-in-elasticsearch-with-block-max-wand

## HW and sizing guidelines
Even though ES scales horizontaly, don't underestimate decent hw. Elatic states that RAM is likely to be the limitation and that 64Gb should be used in each node, cpu is usualy not the bottle neck and 2-8 core cpus likely to cope. The disks should be the fasts affordable. Since ES it self takes care of redundancy any raid beside 0 is never to be used. Be careful if running in a cloude environment since any disc access that is not local is likely to be slow. Does not matter if the SAN/NAS is "fast" there is still network overhead to be accounted for.
Avoid netork latencied as far as possible, there is no support for spanning a cluster across different datacenters. If a failover scenario is needed the cross cluster replication functionality available in the gold/permium is adviced. The latency withina cluster shoudle idealy be <10ms.

However, dont over size machines. If the performance is not enough a new node should keep up with the others, hench using huge machines will need huch investigations to scale. Medium sized machines are easier to spin up more of. Also it is easier to balance different resources such as RAM /CPU.

The shard sizes between 10-40Gb is a good spot. Avoid shardexplosions since each shard adds overhead when it commes to lucene datastructes and cluster state information. However keep in mind that the size of a single segment should never be lager than 5Gb since at that point automatic merges are disabled.

## Tools
<code>GET _cat/thread_pool?v </code>to see utilization
<code>GET _nodes/hot_threads </code>details about what is happaning

# Resumable update by query
Ex starting by adding a index with a single field and indexing a document into it:
```
PUT test
{
  "settings": {
  },
  "mappings": {
    "properties": {
      "msg" : {
        "type": "text"
      }
    }
  }
}
GET test/_mapping
PUT test/_doc/1
{
  "msg" : "HI"
}
GET test/_search
```

Before starting to update the index, add a numeric field to keep track of documents already updated:
```
PUT test/_mapping
{
  "properties": {
    "run" : {
      "type" : "short"
    }
  }
}
GET test/_mapping
GET test/_search
```

Then run the updated wanted and have it limited to only update untouched documents:
```
POST test/_update_by_query
{
  "query": {
    "bool": {
      "must_not": [
        {
          "range": {
            "run": {
              "gte": 1
            }
          }
        }
      ]
    }
  },
  "script" : {
    "source" : """
    if (ctx._source.containsKey("msg")) {
      ctx._source.msg = ctx._source.msg.toLowerCase()
    }
    ctx._source.run = 1;
    """
  }
}
GET test/_search
```

Add a new document and re run the update query:
```
PUT test/_doc/2
{
  "msg" : "BYE"
}
GET test/_search
POST test/_update_by_query
{
  "query": {
    "bool": {
      "must_not": [
        {
          "range": {
            "run": {
              "gte": 1
            }
          }
        }
      ]
    }
  },
  "script" : {
    "source" : """
    if (ctx._source.containsKey("msg")) {
      ctx._source.msg = ctx._source.msg.toLowerCase()
    }
    ctx._source.run = 1;
    """
  }
}
```
As can be seen in the result only one document was updated:
```
{
  "took" : 6,
  "timed_out" : false,
  "total" : 1,
  "updated" : 1,
  "deleted" : 0,
  "batches" : 1,
  "version_conflicts" : 0,
  "noops" : 0,
  "retries" : {
    "bulk" : 0,
    "search" : 0
  },
  "throttled_millis" : 0,
  "requests_per_second" : -1.0,
  "throttled_until_millis" : 0,
  "failures" : [ ]
}
```

Re run the update and verify that no document was updated:
```
GET test/_search
POST test/_update_by_query
{
  "query": {
    "bool": {
      "must_not": [
        {
          "range": {
            "run": {
              "gte": 1
            }
          }
        }
      ]
    }
  },
  "script" : {
    "source" : """
    if (ctx._source.containsKey("msg")) {
      ctx._source.msg = ctx._source.msg.toLowerCase()
    }
    ctx._source.run = 1;
    """
  }
}
```

# Performace
## Query caching 
There is lots to be said about caching in ES. But one easy rule to keep in mind is that any query in filter context is cached as a bitfield. Since no score is calculated the result is a simple 0 or 1 for each document, making it very sutiable for caching and henche it will, making any subsequent queries using the same filter super fast. 