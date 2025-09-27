#!/bin/bash

sqlite3 eda/db.sqlite3 "drop table if exists dove_towers" ".mode csv" ".import dove.csv dove_towers"