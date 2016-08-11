.. Tattle documentation master file, created by
   sphinx-quickstart on Wed Jul  6 16:54:28 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Tattle Intro - Alerting For Your Elasticsearch Data
==============================================

Welcome to Tattle, an alerting tool for your Elasticsearch data.  

Tattle aims to provide you with alerting capabilities for the data stored in your Elasticsearch cluster.  Utilizing powerful Elasticsearch features such as Aggregations and Lucene Query Syntax, coupled together with Tattle's own query language (TQL) our goal is to make alerts that are easy to build and most of all, easy to read (because lets face it, you probably wont be the only one who has to read them)

Overview
--------

Tattle was designed to make use of the powerful features of Elasticsearch (such as Aggregations) to alert us to a multitude of various metrics and log or event type data.  Things such as frequencys, event spikes, aggregation matches, etc all play a big role in our capabilities for alerting.  Coupled together with an extendable ``alert action`` mechanism, Tattle can even fix problems for you as they arise ( using the ``script`` action for example ), notify a Pager Duty Service, or even post to a Slack channel; or all of the above. 


History
--------

Back in 2013 when ELK was farily new term in most people vocabularies, I couldnt find any way to alert on the data inside my Elasticsearch cluster.  Since I was mostly using Elaticsearch to store log, metric and event type data, I couldnt really call ELK a full logging solution until it had the alerting component.  I then decided to build my own system, and "Project Bluenote" was born ( because I didnt have a better name for it at the time (and because I was listening to some old Bluenote records when I wrote the first few lines of code)).  Over the next year or so it was developed on an off in my free time and eventually became an invaluable tool for keeping my site up.  One day, after it alerted me that someone had released some particularly questionable code, they said "Bluenote is such a tattle tale".  Figuring that was a much more appropriate name for the project, Tattle was born.


Requirements
-------------
* Python 2.7
* Virtualenv
* Pip
* Git

Quick Setup & Install
----------------------

Lets assume we will assume will be installing Tattle to ``/opt/Tattle``.
::
    cd /opt
    git clone https://github.com/nickmaccarthy/Tattle
    cd /opt/Tattle
    virtualenv env && source env/bin/activate
    pip install -r requirements.txt

Note: ``$TATTLE_HOME`` refers to where you have installed Tattle.  In the case of this documentation we installed it in ``/opt/Tattle``

Check out the :doc:`install` section for more details.

Or check out the :doc:`tales` section on setting up your first Tale and working with Tattle.



