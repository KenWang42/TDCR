#!/bin/bash

for nMTCD in 1000 3000 5000 10000 30000
do
    python3 circular_grouping.py ${nMTCD}
    echo "circular grouping ${nMTCD} done."
done