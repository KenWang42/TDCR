import pandas as pd
import numpy as np
import random

simRAO = 3000

nMTCD = 30000

nMTCD_success = 0  # total number of device that transmit success

nMTCD_fail = 0  # total number of device that transmit failed

Backoff = 2  # Backoff Indicator = 20ms

maxTrans = 10  # Maximum number of preamble transmission

N_PRB = 25  # Number of Sidelink Physical Resource Block

N_PRB_arrange = 20  # the number of arranged PRB

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
        RA_ready:    Boolean,
                     whether the device can send RA request in the frame
"""
RA_data = MTCD_data[['RA_init', 'RA_first', 'RA_success', 'RA_transmit']]

"""
D2D_member
    records D2D parameter of every Member
    also records numerical result for every Member
    the parametes required in Member -> Header communication
    Index:
        device_id
    Columns 7:
        Header:   Integer,
                  the Header of belonging D2D group
                  also indicate the group Header's device_id
        Member:   Boolen,
                  whether the device is a Member
        arrange:  Integer,
                  indicate the beloneing arrange sequence
        request:  Boolen,
                  whether the Member will send D2D request
        response: Boolean,
                  whether the device received its Header Response
        success:  Integer,
                  the frame the device finish D2D transmission (-1: not success yet)
        transmit: Integer,
                  number of the Member trying to send D2D request
"""
D2D_member = pd.DataFrame(
    columns=['Header', 'Member', 'arrange', 'request', 'response', 'success', 'transmit'],
)

# assign group
D2D_member['Header'] = MTCD_data['clusters']

# assign type
D2D_member['Member'] = (D2D_member.index != D2D_member['Header'])

# assign arrange
for header in D2D_member['Header'].unique():
    members = D2D_member.loc[(D2D_member['Header'] == header) &
                             (D2D_member['Member'])]
    n = 0
    for device_id in members.index:
        D2D_member.at[device_id, 'arrange'] = n // N_PRB_arrange
        n += 1

# initialize request
D2D_member['request'] = np.zeros(nMTCD, dtype=bool)

# initialize response
D2D_member['response'] = np.zeros(nMTCD, dtype=bool)

# initialize success = -1
D2D_member['success'] = np.full(nMTCD, -1)

# initialize transmit
D2D_member['transmit'] = np.zeros(nMTCD, dtype=int)

"""
D2D_group
    records D2D parameter of every Header
    also records numerical result for every Header
    records the parameter required by Header -> Member communication
    Index:
        default sequence
    Columns 6:
        Header:     Integer,
                    device_id of the group Header
        class:      Integer,
                    the barring class of the beloneing D2D group
        N_member:   Integer,
                    the total number of device (member+header) in the group
        N_RA:       Integer,
                    number of RA_request within the group
        arrange:    Integer,
                    current arrange sequence
        HL:         Boolean,
                    whether the group holds more than 38 RA request or not
"""
D2D_group = pd.DataFrame(
    columns=['Header', 'class',
             'N_member', 'N_RA', 'arrange', 'HL']
)

# initialize Header
D2D_group['Header'] = MTCD_data['clusters'].unique()

# assign Class
N_group = len(D2D_group)
N_class = (N_group // N_preamble) + 1
seq = 0
for group in range(N_group):
    D2D_group.at[group, 'class'] = group // N_preamble

# initialize N_member
D2D_group['N_member'] = D2D_member.groupby(['Header']).size().values

# initialize RA_request
D2D_group['N_RA'] = np.zeros(N_group, dtype=int)

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

# initialize class
BS_schedule['class'] = np.zeros(simRAO, dtype=int)

# initialize TDCR
BS_schedule['TDCR'] = np.zeros(simRAO, dtype=int)

"""
class_status
    List[Integer]
    records current status of each class stored in the BS
    update after the class sends RA request
    0: no TDCR frame
    1: 1 TDCR frame in this period, 2 device per group initiate RA
    2: 2 TDCR frame in this period, 1 device per group initiate RA
"""
class_status = [0 for _ in range(N_class)]  # records in BS

class_ptr = 0

D2D_period = 8  # 40 ms Member -> Header, 40ms Header -> Member

SIB2_period = 16  # broadcast period of SIB2: 160ms

for frame in range(simRAO):

    RA_data['RA_ready'] = np.zeros(nMTCD, dtype=bool)  # reset RA_ready

    if frame % SIB2_period == 0:  # SIB2 broadcast
        if frame + SIB2_period < simRAO:
            schedule = BS_schedule.loc[frame:(frame + SIB2_period)]
        if 1 in class_status:
            BS_schedule.at[schedule.index[0], 'TDCR'] = 1
        elif 2 in class_status:
            BS_schedule.at[schedule.index[0], 'TDCR'] = 2
            BS_schedule.at[schedule.index[1], 'TDCR'] = 2
        for c in range(N_class):
            # s: the frames for class c within next period
            s = schedule.loc[(schedule['class'] == c)]
            if class_status[c] == 1:
                BS_schedule.at[s.index[0], 'TDCR'] = 1
            elif class_status[c] == 2:
                BS_schedule.at[s.index[0], 'TDCR'] = 2
                BS_schedule.at[s.index[1], 'TDCR'] = 2

    # generate D2D request
    devices = RA_data.loc[(RA_data['RA_init'] == frame)
                          & (RA_data['RA_transmit'] <= maxTrans)]
    for device_id in devices.index:
        D2D_member.at[device_id, 'request'] = True
        D2D_member.at[device_id, 'response'] = False

    if frame % (D2D_period) == 3:  # Members' request
        members = D2D_member.loc[(D2D_member['request'])
                                 & D2D_member['Member']]
        headers = members['Header'].unique()
        for header in headers:

            group_id = D2D_group.loc[D2D_group['Header'] == header].index[0]

            cur_arrange = D2D_group.at[group_id, 'arrange']

            group_members = members.loc[D2D_member['request'] == header]

            arr_members = group_members.loc[group_members['arrange']
                                            == cur_arrange]

            non_arr_members = group_members.loc[group_members['arrange']
                                                != cur_arrange]

            framePRB = [[] for _ in range(N_PRB)]

            for arr_member in arr_members.index:
                # compete arranged-PRB
                framePRB[random.randrange(N_PRB_arrange)].append(arr_member)
                D2D_member.at[arr_member, 'transmit'] += 1

            for non_arr_member in non_arr_members.index:
                # compete non-arranged-PRB
                framePRB[random.randrange(N_PRB_arrange, N_PRB)].append(
                    non_arr_member)
                D2D_member.at[non_arr_member, 'transmit'] += 1

            for PRB in range(N_PRB):
                # check for the D2D request
                members = framePRB[PRB]
                if len(members) == 1:  # D2D request success
                    D2D_group.at[group_id, 'N_RA'] += 1
                    member_id = members[0]
                    D2D_member.at[member_id, 'request'] = False
                    D2D_member.at[member_id, 'response'] = True
                    D2D_member.at[member_id, 'success'] = frame
            
            if D2D_member.at[header, 'request']:
                D2D_group.at[group_id, 'N_RA'] += 1
                D2D_member.at[header, 'request'] = False
                D2D_member.at[header, 'response'] = True

            if D2D_group.at[group_id, 'N_RA'] >= 38:
                # more than 38 devices within the group initiates RA_request
                D2D_group.at[group_id, 'HL'] = True
            else:
                D2D_group.at[group_id, 'HL'] = False

        # Header Response

        class_ = BS_schedule.at[frame, 'class']
        TDCR = BS_schedule.at[frame, 'TDCR']
        class_groups = D2D_group.loc[D2D_group['class'] == class_]

        for header in class_groups['Header']:
            # Choose device to initiate RA procedure
            valid_group_members = D2D_member.loc[(D2D_member['Header'] == header) & (D2D_member['response'])]
            if TDCR == 0 or TDCR == 2:  # 1 device with max transmit
                device_id = valid_group_members['transmit'].idxmax()
                RA_data.at[device_id, 'RA_ready'] = True
            elif TDCR == 1:  # 2 device with max transmit
                device_id_0 = valid_group_members['transmit'].idxmax()
                RA_data.at[device_id_0, 'RA_ready'] = True
                valid_group_members = valid_group_members.drop(device_id)
                device_id_1 = valid_group_members['transmit'].idxmax()
                RA_data.at[device_id_1, 'RA_ready'] = True
        
        # RA Procedure

        RA_devices = RA_data.loc[RA_data['RA_ready']]

        if TDCR == 0:  # assign every device with 1 preambles, no collision
