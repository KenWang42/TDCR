import pandas as pd
import numpy as np
import random

simRAO = 3000

nMTCD = 30000

nMTCD_success = 0  # total number of device that transmit success

nMTCD_fail = 0  # total number of device that transmit failed

Backoff = 2  # Backoff Indicator = 20ms

maxTrans = 10  # Maximum number of preamble transmission

arrangePRB = 20  # the number of arranged PRB

N_preamble = 54  # Number of PRACH Preamble

MTCD_data = pd.read_csv(f'MTCD_data_{nMTCD}.csv', index_col=False)

"""
Preamble_status
    records the status of PRACH Preamble in every system frame (10ms)
    Index:
        system frame
    Columns:
        N_request: Integer,
                   number of device that initiate RA request
        empty:     Integer,
                   number of preamble choose by no one
        collided:  Integer,
                   number of preamble choose by multiple devices
        success:   Integer,
                   number of preamble choose by exactly 1 device
"""
Preamble_status = pd.DataFrame(
    columns=['nRA', 'empty', 'collided', 'success'],
)
Preamble_status.index.name = 'system frame'

"""
RA_data
    records RA parameter and simulation result of every device
    the parameters required in enB <-> device communication
    Index:
        device_id
    Columns 4:
        RA_init:     Integer,
                     next frame the device send RA request
        RA_first:    Integer,
                     first frame the device send RA request
        RA_success:  Integer,
                     frame the device complete RA procedure
        RA_transmit: Integer,
                     number of the device trying to send RA request
"""
RA_data = MTCD_data[['RA_init', 'RA_first', 'RA_success', 'RA_transmit']]
RA_data.index.name = 'device_id'

"""
D2D_member
    records D2D parameter of every Member
    also records numerical result for every Member
    the parametes required in Member -> Header communication
    Index:
        device_id
    Columns 6:
        group:    Integer,
                  the beloneing D2D group
                  also indicate the group Header's device_id
        Member:   Boolen,
                  whether the device is a Member
        arrange:  Integer,
                  indicate the beloneing arrange sequence
        request:  Boolen,
                  whether the Member will send D2D request
        delay:    Integer,
                  total delay of D2D transmission
        transmit: Integer,
                  number of the Member trying to send D2D request
"""
D2D_member = pd.DataFrame(
    columns=['group', 'Member', 'arrange', 'request', 'delay', 'transmit'],
)

# assign group
D2D_member['group'] = MTCD_data['clusters']

# assign type
D2D_member['Member'] = (D2D_member.index != D2D_member['group'])

# assign arrange
for group in D2D_member['group'].unique():
    members = D2D_member.loc[(D2D_member['group'] == group) &
                             (D2D_member['Member'])]
    n = 0
    for device_id, member in members.iterrows():
        D2D_member.at[device_id, 'arrange'] = n // arrangePRB
        n += 1

# initialize request
D2D_member['request'] = np.zeros(nMTCD, dtype=bool)

# initialize delay
D2D_member['delay'] = np.zeros(nMTCD, dtype=int)

# initialize transmit
D2D_member['transmit'] = np.zeros(nMTCD, dtype=int)

"""
D2D_group
    records D2D parameter of every Header
    also records numerical result for every Header
    records the parameter required by Header -> Member communication
    Index:
        default sequence
    Columns 5:
        Header:     Integer,
                    device_id of the group Header
        class:      Integer,
                    the barring class of the beloneing D2D group
        N_member:   Integer,
                    the total number of member in the group
        RA_request: Integer,
                    number of RA_request within the group
        arrange:    Integer,
                    current arrange sequence
        HL:         Boolean,
                    whether the group holds more than 38 RA request or not
"""
D2D_group = pd.DataFrame(
    columns=['Header', 'class', 'N_member', 'RA_request', 'arrange', 'HL'],
)

# initialize Header
D2D_group['Header'] = MTCD_data['clusters'].unique()

# assign Class
N_group = len(D2D_group)
N_class = (len(D2D_Group) // N_preamble) + 1
D2D_group['class'] = [c // N_preamble for c in range(N_group)]

# initialize RA_request
D2D_group['RA_request'] = np.zeros(N_group, dtype=int)

# initialize current arrange sequence
D2D_group['arrange'] = np.zeros(N_group, dtype=int)

# initialize HL status
D2D_group['HL'] = np.zeros(N_group, dtype=bool)

"""
BS_schedule
    indicate the broadcast information for SIB2
    update every 16 system frame
    Do not require initialize
    Index:
        system_frame
    Columns 2:
        class: Integer,
               the class can initiate RA procedure
        TDCR:  Integer,
               the TDCR level of the frame
               0: no TDCR frame
               1: 1 TDCR frame in this period, 2 device per group initiate RA
               2: 2 TDCR frame in this period, 1 device per group initiate RA
"""
BS_schedule = pd.DataFrame(
    columns=['class', 'TDCR'],
)

# assign class of every frame
BS_schedule['class'] = [f % N_class for f in range(simRAO)]

# initialize TDCR
BS_schedule['class'] = np.zeros(simRAO, dtype=int)

"""
class_status
    List[Integer]
    records current status of each class stored in the BS
    update after the class sends RA request
    0: no TDCR frame
    1: 1 TDCR frame in this period, 2 device per group initiate RA
    2: 2 TDCR frame in this period, 1 device per group initiate RA
"""
class_status = [0 for _ in range(N_class)]

D2D_period = 8  # 40 ms Member -> Header, 40ms Header -> Member

SIB2_period = 16  # broadcast period of SIB2: 160ms

for frame in range(simRAO):

    if frame % SIB2_period == 0:  # SIB2 broadcast
        if frame + SIB2_period < simRAO:
            schedule = BS_schedule.loc[np.arange(
                frame, frame + SIB2_period)]
        else:
            schedule = BS_schedule.loc[frame:]
        for c in range(N_class):
            s = schedule.loc[(schedule['class'] == c)]
            if class_status[c] == 1:
                BS_schedule.at[s.index[0], 'TDCR'] = 1
            elif class_status[c] == 2:
                BS_schedule.at[s.index[0], 'TDCR'] = 2
                BS_schedule.at[s.index[1], 'TDCR'] = 2

    if frame % (D2D_period) == 3:  # Members' request
        ...

    if frame % (D2D_period) == 4:  # Header response
        ...

    # RA Procedure
