import pandas as pd
import numpy as np
import random

simRAO = 2000

nMTCD = 30000

nMTCD_success = 0

nMTCD_fail = 0

# Backoff Indicator = 20ms
Backoff = 2

# Maximum number of preamble transmission
maxTrans = 10

# PreambleStatus
# index: 'preamble_id'
# columns: 'nRA', 'empty', 'collided', 'success'

PreambleStatus = pd.DataFrame(
    np.zeros((simRAO, 4), dtype=int),
    columns=['nRA', 'empty', 'collided', 'success'],
)
PreambleStatus.index.name = 'system frame'

# MTCD_data
# index: 'MTCD_id'
# position related columns:
#     x, y, clusters
# time related columns:
#     RA_init, RA_first, RA_success, RA_transmit

MTCD_data = pd.read_csv(f'MTCD_data_{nMTCD}.csv', index_col=False)

nMTCD = 30000

arrangePRB = 20
EAB = 1