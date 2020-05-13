#!/bin/bash

for nMTCD in 10000 30000
do
    python3 ACB_0.5.py ${nMTCD}
    echo "ACB 0.5 with ${nMTCD} devices done."
done