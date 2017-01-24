#!/bin/bash

source env/bin/activate
cd docs
make html
deactivate
