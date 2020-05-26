import random
import pandas as pd
import numpy as np
from scipy.stats import beta

# The number of MTC Devices
nMTCD = 1000

# time duration of simulation, 1 RAO = 10ms
simRAO = 1000

# dataframe of result of RA Time related
RA_Time = pd.DataFrame(
    columns=['RA_init', 'RA_first', 'RA_success', 'RA_transmit'])

# number of RA in every system frame
nMTCD_frame = np.zeros(simRAO)

# generate cdf of beta distribution
a = 3
b = 4
x = np.linspace(0, 1, simRAO)
beta_cdf = beta.cdf(x, a, b)

# generate RA time in each MTCD by beta distribution
for device in range(nMTCD):
    p = random.random()
    for frame in range(simRAO):
        if p < beta_cdf[frame]:
            RA_Time.loc[device] = [frame, frame, -1, 0]
            nMTCD_frame[frame] += 1
            break

RA_Time.to_csv(f'MTCD_RA_Time/MTCD_RA_Time_{nMTCD}.csv', index=False)
pd.DataFrame(nMTCD_frame).to_csv(f'nMTCD_per_RAO/nMTCD_per_RAO_{nMTCD}.csv', index=False)
