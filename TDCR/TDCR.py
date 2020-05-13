import pandas as pd
import numpy as np
import random

simRAO = 2000

nMTCD = 30000

nMTCD_success = 0  # total number of device that transmit success

nMTCD_fail = 0  # total number of device that transmit failed

Backoff = 2  # Backoff Indicator = 20ms

maxTrans = 10  # Maximum number of preamble transmission

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
    np.zeros((simRAO, 4), dtype=int),
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

"""
D2D_member
    records D2D parameter of every Member
    also records numerical result for every Member
    the parametes required in Member -> Header communication
    Index:
        device_id
    Columns 4:
        clusters: Integer,
                  the beloneing D2D group
                  also indicate the group Header's device_id
        type:     Boolen,
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
data = ...
D2D_member = pd.DataFrame(
    data,
    columns=['clusters', 'type', 'arrange', 'request'],
)
D2D_member['clusters'] = MTCD_data['clusters']

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
                    whether the group is Heavy Loading or not
"""

"""
BS_schedule
    indicate the broadcast information for SIB2
    update every 16 system frame
    Index:
        system_frame
    Columns 2:
        class: Integer,
               the class can initiate RA procedure
        TDCR:  Bollean,
               whether the frame is a TDCR frame
"""

"""
TDCR_result
    records the simulation result for numerical analysis
    Index:
        system frame
    Columns:
        TDCR: List[Boolean]
                  whether the class is HL

"""

nMTCD = 30000
arrangePRB = 20
EAB = 1

for frame in range(simRAO):
    
    # record PRACH Preamble status in each frame
    framePreambles = [[] for _ in range(55)]
