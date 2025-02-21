#!/bin/bash

WORKSPACE=/home/bbell/sandbox/projects/personal/reading_tracker/reading_list

python -m venv venv

source venv/bin/activate  # On Windows use: venv\Scripts\activate

pip install -e .

python setup.py

