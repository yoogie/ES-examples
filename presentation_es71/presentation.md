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

## pipeline
Since there has been a lot of work done in the ingest pipeline world, a logical edition is also the pipeline processor. It makes it possible to reuse pipelines. I.e apply the same pice of logic into multiple workflows. Something to notice here though is that only the final result of all processing is what will enter the elasticsearch database. 
We had a missunderstanding when this processor was first relesed and tried to reuse some logic that dropted a document in one pipeline and would index it in an other. However, if droped in one it is droped in all.

Ex:

```
```
Result:

```
```
# Beats?
## ECS?
Any good example for common schema?
## Module?
Create our own module, add kibana queries etc. Have it implement ECS?