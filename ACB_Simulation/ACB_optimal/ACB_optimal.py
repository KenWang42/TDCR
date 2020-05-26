import pandas as pd
import numpy as np
import random
import sys

simRAO = 2000

nMTCD = int(sys.argv[1])

nMTCD_success = 0

nMTCD_fail = 0

# Backoff Indicator = 20ms
Backoff = 2

# Maximum number of preamble transmission
maxTrans = 10

N_preamble = 54

# PreambleStatus
# index: 'preamble_id'
# columns: 'nRA', 'empty', 'collided', 'success'

PreambleStatus = pd.DataFrame(
    np.zeros((simRAO, 4), dtype=int),
    columns=['nRA', 'empty', 'collided', 'success'],
)
PreambleStatus.index.name = 'system frame'

# RAtime
# index: 'device_id'
# columns: 'RA_init', 'RA_first', 'RA_success', 'RA_transmit'

RAtime = pd.read_csv(f'MTCD_RA_Time_{nMTCD}.csv', index_col=False)


for frame in range(simRAO):
    framePreambles = [[] for _ in range(N_preamble)]
    devices = RAtime.loc[(RAtime['RA_init'] == frame) & (RAtime['RA_transmit'] <= maxTrans)]
    n = len(devices)
    ACBP = N_preamble / n if n > N_preamble else 1
    for device_id in devices.index:
        q = random.random()

        #  ACB blocking

        if q < ACBP:
            PreambleStatus.iloc[frame]['nRA'] += 1
            framePreambles[random.randrange(N_preamble)].append(device_id)

        else:

            RAtime.iloc[device_id]['RA_init'] += int((0.7 + 0.6 * random.random())*40)

    for preamble in range(N_preamble):
        n = framePreambles[preamble]
        if len(n) == 0:  # empty preamble
            PreambleStatus.iloc[frame]['empty'] += 1
        elif len(n) == 1:  # success preamble
            nMTCD_success += 1
            PreambleStatus.iloc[frame]['success'] += 1
            device_id = framePreambles[preamble][0]
            RAtime.iloc[device_id]['RA_success'] = frame
            RAtime.iloc[device_id]['RA_transmit'] += 1
        else:
            PreambleStatus.iloc[frame]['collided'] += 1
            for device_id in framePreambles[preamble]:
                reTransmit = RAtime.iloc[device_id]['RA_transmit']
                reTransmit += 1
                if reTransmit > maxTrans:
                    nMTCD_fail += 1
                else:
                    RAtime.iloc[device_id]['RA_init'] += random.randrange(
                        1, Backoff)
        if nMTCD_fail + nMTCD_success >= nMTCD:
            break

RAtime.to_csv(f'result/ACB_optimal_Device_Result_{nMTCD}.csv', index=False)
PreambleStatus.to_csv(f'result/ACB_optimal_Preamble_Status_{nMTCD}.csv', index=False)
