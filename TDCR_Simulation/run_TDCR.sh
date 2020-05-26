#!/bin/bash
for nMTCD in 10000 30000
do
    python3 TDCR.py ${nMTCD}
    echo "TDCR with ${nMTCD} devices done."
done