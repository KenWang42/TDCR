#!/bin/bash

for nMTCD in 10000 30000
do
    python3 STD.py ${nMTCD}
    echo "STD with ${nMTCD} devices done."
done