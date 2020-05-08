#!/bin/bash

for PACB in 1 2 4 8 16 32
do
    python3 ACB_var_10k.py ${PACB}
    echo "ACB 1/${PACB} done."
done