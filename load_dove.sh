#!/bin/bash

sqlite3 "drop table if exists dove_towers" ".mode csv" ".import dove.csv dove_towers"