[![Build Status](https://travis-ci.org/nickmaccarthy/Tattle.svg?branch=master)](https://travis-ci.org/nickmaccarthy/Tattle.svg?branch=master)

# Tattle
### Alerting For Your Elasticsearch Data 

Before you begin, please read the full documentation for Tattle here:  https://tattle.readthedocs.io/en/latest/intro.html 

Welcome to Tattle, an alerting tool for your Elasticsearch data.  

Tattle aims to provide you with alerting capabilities for the data stored in your Elasticsearch cluster.  Utilizing powerful Elasticsearch features such as Aggregations and Lucene Query Syntax, coupled together with Tattle's own query language (TQL) our goal is to make alerts that easy to build and most of all, easy to read (because lets face it, you probably wont be the only one who has to read them)

## Overview

Tattle was designed to make use of the powerful features of Elasticsearch (such as Aggregations) to alert us to a multitude of various metrics and log or event type data.  Things such as frequencys, event spikes, aggregation matches, etc all play a big role in our capabilities for alerting.  Coupled together with an extendable ``alert action`` mechanism, Tattle can even fix problems for you as they arise ( using the ``script`` action for example ), notify a Pager Duty Service, or even post to a Slack channel; or all of the above. 

## History

Back in 2013 when ELK was farily new term in most people vocabularies, I couldnt find any way to alert on the data inside my Elasticsearch cluster.  Since I was mostly using Elaticsearch to store log, metric and event type data, I couldnt really call ELK a full logging solution until it had the alerting component.  I then decided to build my own system, and "Project Bluenote" was born ( because I didnt have a better name for it at the time (and because I was listening to some old Bluenote records when I wrote the first few lines of code)).  Over the next year or so it was developed on an off in my free time and eventually became an invaluable tool for keeping my companys site up.  One day, after it alerted me that someone had released some particularly questionable code, they said "Bluenote is such a tattle tale".  Figuring that was a much more appropriate name for the project, Tattle was born.

## Requirements

* Python 2.7, Python 3.3+
* Virtualenv
* Pip
* Git

## Documentation

Read the full documentation for Tattle here:  https://tattle.readthedocs.io/en/latest/intro.html
