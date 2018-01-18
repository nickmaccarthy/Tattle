[![Build Status](https://travis-ci.org/nickmaccarthy/Tattle.svg?branch=master)](https://travis-ci.org/nickmaccarthy/Tattle.svg?branch=master)

# Tattle
### Alerting For Your Elasticsearch Data 

Welcome to Tattle, an alerting tool for your Elasticsearch data.  

Tattle aims to provide you with alerting capabilities for the data stored in your Elasticsearch cluster.  Utilizing powerful Elasticsearch features such as Aggregations and Lucene Query Syntax, coupled together with Tattle's own query language (TQL) our goal is to make alerts that easy to build and, easy to read (because lets face it, you probably wont be the only one who has to read them)

Before you begin, please take a look at the full documentation for Tattle here:  https://tattle.readthedocs.io/en/latest/intro.html 

## Overview

Tattle was designed to make use of the powerful features of Elasticsearch (such as Aggregations) to alert us to a multitude of various metrics and log or event type data.  Things such as frequencys, event spikes, aggregation matches, etc all play a big role in our capabilities for alerting.  Coupled together with an extendable ``alert action`` mechanism, Tattle can even fix problems for you as they arise ( using the ``script`` action for example ), notify a Pager Duty Service, or even post to a Slack channel; or all of the above. 


## Quick Install
**Note** This will assume we will be installing into `/opt/Tattle`

1. Ensure the Requirements are met 
2. Run the following commands:
```
cd /opt
git clone https://github.com/nickmaccarthy/Tattle
cd /opt/Tattle
virtualenv env && source env/bin/activate
pip install -r requirements.txt
```
3. Now set up some Tales, read the docs @  https://tattle.readthedocs.io/en/latest/intro.html
4. ??
5. Profit 

## Requirements

* Python 2.7, Python 3.4+
* Virtualenv
* Pip
* Git

## Documentation

Read the full documentation for Tattle here:  https://tattle.readthedocs.io/en/latest/intro.html
