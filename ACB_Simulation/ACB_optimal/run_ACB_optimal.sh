#!/bin/bash

for nMTCD in 10000 30000
do
    python3 ACB_optimal.py ${nMTCD}
    echo "ACB optimal with ${nMTCD} devices done."
done