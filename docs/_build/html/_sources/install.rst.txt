Getting Started - Install & Setup
=================================

Installing Tattle is pretty simple process. Tattle was written in Python, and was designed to work within a `virtualenv <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_.  Tattle works with both Python 2.7 and Python 3.3+ (it was tested against Python 3.5, which is the latest at the time of this writing).  

The first steps for getting Tattle installed are ensuring you have either Python 2.7 or Python 3.3+ installed on your system, as well as `pip <https://pypi.python.org/pypi/pip>`_ and `virtualenv <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_ ( typically installing python 2.7 on a modern linux system is as easy as ``apt-get install python27 python27-virtualenv python27-pip`` for Debian based systems (such as Ubuntu) or ``yum install python27 python27-pip python27-virtualenv`` for CentOS based users )

.. note::
    If you already have python 2.7.10 or above installed, then you should already have `pip`.  You can typically install virtualenv with pip as well

After `Python 2.7`, `pip` and `virtualenv` have been installed, you will need ensure you have `git` installed ( ``apt-get install git``) to clone the repository where Tattle is located. 

.. note::
    We use git to pull down the source code for Tattle.  If you dont have or want to install `git`, you can also download the zip file for Tattle from the `Tattle Github <https://github.com/nickmaccarthy/Tattle>`_ page and unzip it manually to a directory of your choice.  

After you have these base applications installed, check our the :ref:`setup-tattle` section to continue.

Code
-------------------

The source code for Tattle is located on Github:  https://github.com/nickmaccarthy/Tattle

Requirements
--------------------
* Python 2.7 or Python 3.3+
* Virtualenv
* Pip
* Git

.. _setup-tattle:

Setup & Install
-------------------
For the sake of this documentation we will be installing Tattle to ``/opt/Tattle``.  If you wish to install Tattle into a different location, simply replace ``/opt/tattle`` with your install directory.
::
    cd /opt
    git clone https://github.com/nickmaccarthy/Tattle
    cd /opt/Tattle
    virtualenv env && source env/bin/activate
    pip install -r requirements.txt

.. note::
    Throughout the rest of this documentation, you will see reference to ``$TATTLE_HOME``.  This is a variable to represent where Tattle was installed.   In the case of this documentation we installed it in ``/opt/Tattle``

.. _configure-tattle:

Configuration
--------------

There are a few things we need to configure before we can start using Tattle.

 
1. We need to define how to connect to our Elasticserach cluster.  To do this, simple edit ``$TATTLE_HOME/etc/tattle/elasticsearch.yaml``

.. note::
    There are example configuration files in the ``$TATTLE_HOME/examples`` directory you can use for reference.  In this case, You can use the included ``$TATTLE_HOME/examples/elasticsearch.yaml`` as guidance.

Example
::
    servers:
        - "elasticsearch.mycompany.com"
    args:
        port: 9200
        use_ssl: false
        timeout: 30

.. note::
    The above YAML reference uses the directives defined the python elasticsearch client.  The variables for the args can be found here: https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch

2. We need to define our email configuration, and or other alert output configurations such as pagerduty, slack, etc.  In this case will just set up our email output.  
Create a new file called ``$TATTLE_HOME/etc/tattle/email.yaml``

Example
::
        server: 'localhost'
        port: 25
        default_sender: 'tattle@localhost'
        subject_prefix: "Tattle Alert: "

3. Now we need to make `Tale`.  A `Tale` is a definition for our alert.  As Tales are specific to the type of data you need to alert on, they will require more a more in-depth explination then what we can provide in this section.   So please go check out the :doc:`tales` section on setting up a Tale, and come back to the next step once that is completed.


4. Once you have configured your Tale, please look at the :ref:`running-tattle` section below.

.. note::
    A note on yaml configuration files.  You can use use both ``.yml`` or ``.yaml`` as your file extension

.. _running-tattle:


Environment Variables
-----------------------

Tattle can also support `environment variables` for configuration locations.  This is useful if you wanted to place your Tattle configurations in a directory other than ``$TATTLE_HOME``, and makes container applications such a docker easier to implement.  

$TATTLE_CONFIG_DIR
~~~~~~~~~~~~~~~~~~~
``$TATTLE_CONFIG_DIR`` is the location where Tattle will search for its config files like, ``tattle.yml``, ``elasticserach.yml``, ``pagerduty.yml``, etc

$TATTLE_TALES
~~~~~~~~~~~~~~~~~~~
``$TATTLE_TALES`` is the location where Tattle will search for Tales. 

.. note::
    You can specify multiple directories in Environment Variables by delimiting them with a ``:``.  For example if we wanted to search our home dir and ``/etc/tattle/tatles``, we could use ``$TATTLE_TALES=/home/myuser/tales:/etc/tattle/tales``


Running
--------

1. Tattle is designed (in its current form) to run standalone.  Its best to run Tattle on a CRON job, typically with an interval of every minute.  You can run it manually yourself as well. Just run ``$TATTLE_HOME/bin/tattled.py``.  

.. note::
    There are thoughts of having Tattle run as daemon in the future. 

2. Tattle also comes with a tale/alert testing utility.  This is how you can check your Tale before you put it into 'production'.  If there are matches, tattle will run whatever is in the Tale ``action``.  Simply run ``$TATTLE_HOME/bin/test_alert.py  /path/to/the/tale.yaml``. 

.. _example-cron:

Example Cron
-------------------
Its typical for Tattle run on a CRON job, with a one minute interval.  Everytime Tattle runs, it will check all alerts/Tales.  So if you add additonal tales, Tattle should pick them on its next run

``*/1 * * * * /opt/Tattle/env/bin/python /opt/Tattle/bin/tattled.py``
