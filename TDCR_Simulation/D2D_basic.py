import pandas as pd
import numpy as np
import random
import os
import sys
import time

start_time = time.time()

path = os.path.abspath('.')

simRAO = 3000

nMTCD = int(sys.argv[1])

nMTCD_success = 0  # total number of device that transmit success

nMTCD_fail = 0  # total number of device that transmit failed

Backoff = 2  # Backoff Indicator = 20ms

maxTrans = 10  # Maximum number of preamble transmission

N_PRB = 25  # Number of Sidelink Physical Resource Block

N_PRB_arrange = N_PRB  # the number of arranged PRB

TDCR_Threshold = 30000

N_preamble = 54  # Number of PRACH Preamble

file_path = path + f'/MTCD_data_{nMTCD}.csv'
MTCD_data = pd.read_csv(file_path, index_col=False)

"""
RA_data
    records RA parameter and simulation result of every device
    the parameters required in enB <-> device communication
    Index:
        device_id
    Columns 3:
        RA_init:     Integer,
                     next frame the device send RA request
        RA_first:    Integer,
                     first frame the device send RA request
        RA_success:  Integer,
                     frame the device complete RA procedure
        RA_transmit: Integer,
                     number of the device trying to send RA request
"""
RA_data = MTCD_data[['RA_init', 'RA_success', 'RA_transmit', 'RA_first']]

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
    columns=['Header', 'Member', 'arrange',
             'request', 'response', 'success', 'transmit'],
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
        arr_seq:    Integer,
                    current arrange sequence
        N_RA:       Integer,
                    number of RA_request within the group
        HL:         Bollean,
                    Whether the group is in HL or not
"""
D2D_group = pd.DataFrame(
    columns=['Header', 'class', 'N_member', 'arr_seq', 'N_RA', 'HL']
)

# initialize Header
D2D_group['Header'] = MTCD_data['clusters'].unique()

# assign Class
N_group = len(D2D_group)
N_Class = (N_group // N_preamble) + 1
seq = 0
for group in range(N_group):
    D2D_group.at[group, 'class'] = group // N_preamble

# initialize N_member
D2D_group['N_member'] = D2D_member.groupby(['Header']).size().values

# initialize current arrange sequence
D2D_group['arr_seq'] = np.zeros(N_group, dtype=int)

# initialize N_RA
D2D_group['N_RA'] = np.zeros(N_group, dtype=int)

# initialize N_RA
D2D_group['HL'] = np.zeros(N_group, dtype=bool)

"""
BS_schedule
    indicate the broadcast information for SIB2
    update every 16 system frame
    Do not require initialize
    Index:
        system_frame
    Columns 2:
        class: List[Integer],
               the class can initiate RA procedure
        TDCR:  Char,
               indicate the type of TDCR level
               N:  normal loading, not a TDCR frame
               M:  medium loading congestion resolving
                   1 frame per period
                   2 RA_request per group
               H:  heavy loading congestion resolving
                   2 frame per period
                   1 RA_request per group
"""
BS_schedule = pd.DataFrame(
    columns=['class', 'TDCR'],
)

"""
D2D_result
    records the numerical result of D2D sidelink
    Index:
        sequence of SC-Period
    Columns 4:
         frame:      Integer,
                     the system frame when the SC-period-1 ends
         N_request:  Integer,
                     number of device send D2D_request to its header
         N_response: Integer,
                     number of D2D device that receive its Header response
         N_HL:       Integer,
                     number of Heavy Loading D2D_group
"""
D2D_result = pd.DataFrame(
    columns=['frame', 'N_request', 'N_response', 'N_HL'],
)

"""
RA_result
    records the numerical result of Random Access
    Index:
        system frame
    Columns 5:
        TDCR:
        N_RA:
        empty:
        collided:
        success:
"""

RA_result = pd.DataFrame(
    columns=['N_RA', 'empty', 'collided', 'success', 'TDCR'],
)

#  records the current loading status of each classes
Class_Status = ['N'] * N_Class

D2D_period = 8  # 40 ms Member -> Header, 40ms Header -> Member

SIB2_period = 16  # broadcast period of SIB2: 160ms

N_Normal_frame_total = 0

for frame in range(simRAO):
    # generate D2D request

    devices = RA_data.loc[(RA_data['RA_init'] == frame)
                          & (RA_data['RA_success'] == -1)
                          & (RA_data['RA_transmit'] <= maxTrans)]

    D2D_member.loc[devices.index, 'request'] = True
    D2D_member.loc[devices.index, 'response'] = False

    if frame % (SIB2_period) == 0:  # SIB2 update
        N_Normal_frame = SIB2_period
        M_Class = []
        H_Class = []
        for i in range(N_Class):  # check status of each Classes
            if Class_Status[i] == 'H':
                H_Class.append(i)
            elif Class_Status[i] == 'M':
                M_Class.append(i)
        if len(H_Class) != 0:
            for i in range(2):
                BS_schedule = BS_schedule.append(
                    {'class': H_Class, 'TDCR': 'H'}, ignore_index=True)
            N_Normal_frame -= 2

        if len(M_Class) != 0:
            BS_schedule = BS_schedule.append(
                {'class': M_Class, 'TDCR': 'M'}, ignore_index=True)
            N_Normal_frame -= 1

        for i in range(N_Normal_frame):
            BS_schedule = BS_schedule.append(
                {'class': [N_Normal_frame_total % N_Class], 'TDCR': 'N'}, ignore_index=True)
            N_Normal_frame_total += 1

    if frame % (D2D_period) == 4:  # D2D update
        members_ = D2D_member.loc[D2D_member.request].copy()
        N_D2D_request = len(members_)
        N_D2D_response = N_HL = 0
        headers = members_['Header'].unique()
        for header in headers:
            # Members' request
            group_id = D2D_group.loc[D2D_group['Header'] == header].index[0]

            cur_arrange = D2D_group.at[group_id, 'arr_seq']

            group_members = members_.loc[(members_.Header == header)]

            # arr_members = group_members.loc[group_members.arrange ==
            #                                 cur_arrange].index

            # non_arr_members = group_members.loc[group_members.index.difference(
            #     arr_members)].index

            framePRB = [[] for _ in range(N_PRB)]

            for member_id in group_members.index:
                if member_id == header:  # header itself
                    D2D_member.at[header, 'response'] = True
                else:  # compete for PRB
                    framePRB[random.randrange(N_PRB)].append(member_id)
                D2D_member.at[member_id, 'transmit'] += 1

            # for arr_member in arr_members:  # compete for arranged-PRB
            #     framePRB[random.randrange(N_PRB_arrange)].append(arr_member)
            #     D2D_member.at[arr_member, 'transmit'] += 1

            # for non_arr_member in non_arr_members:
            #     if non_arr_member == header:  # header itself
            #         D2D_member.at[header, 'response'] = True
            #     else:  # compete for non-arranged-PRB
            #         framePRB[random.randrange(N_PRB_arrange, N_PRB)].append(
            #             non_arr_member)
            #     D2D_member.at[non_arr_member, 'transmit'] += 1

            for PRB in range(N_PRB):
                PRB_members = framePRB[PRB]
                if len(PRB_members) == 1:  # sending Header Response
                    member_id = PRB_members[0]
                    D2D_member.at[member_id, 'request'] = False
                    D2D_member.at[member_id, 'response'] = True
                    D2D_member.at[member_id, 'success'] = frame
                    D2D_group.at[group_id, 'N_RA'] += 1
                    N_D2D_response += 1

            # arrange PRB sequence update
            # D2D_group.at[group_id, 'arr_seq'] += 1
            # max_arr = D2D_group.at[group_id, 'N_member'] // N_PRB_arrange
            # if D2D_group.at[group_id, 'arr_seq'] > max_arr:
            #     D2D_group.at[group_id, 'arr_seq'] = 0

            # update Group status
            if D2D_group.at[group_id, 'N_RA'] >= TDCR_Threshold:
                D2D_group.at[group_id, 'HL'] = True
                N_HL += 1
            else:
                D2D_group.at[group_id, 'HL'] = False

        D2D_result.loc[len(D2D_result)] = [
            frame, N_D2D_request, N_D2D_response, N_HL]

    # RA Procedure
    TDCR = BS_schedule.at[frame, 'TDCR']
    N_RA = 0
    N_Success = 0
    N_Collided = 0
    class_list = BS_schedule.at[frame, 'class']
    devices_list = []  # list for RA compete
    groups_in_class = pd.DataFrame()

    if TDCR == 'N':  # Normal frame
        for class_ in class_list:
            groups_in_class = groups_in_class.append(
                D2D_group.loc[D2D_group['class'] == class_])

        for header in groups_in_class['Header']:
            # Choose device to initiate RA procedure
            members_in_group = D2D_member.loc[(
                D2D_member.Header == header) & (D2D_member.response)]
            if not len(members_in_group):
                continue
            chosen_device = members_in_group['transmit'].idxmax()
            header_id = D2D_member.at[chosen_device, 'Header']
            D2D_group.loc[D2D_group['Header'] == header_id, 'N_RA'] -= 1
            RA_data.at[chosen_device, 'RA_success'] = frame
            RA_data.at[chosen_device, 'RA_transmit'] += 1
            D2D_member.at[chosen_device, 'request'] = False
            D2D_member.at[chosen_device, 'response'] = False
            N_RA += 1
            N_Success += 1
            nMTCD_success += 1

    elif TDCR == 'M':  # Middle loading TDCR frame
        for class_ in class_list:
            groups_in_class = groups_in_class.append(
                D2D_group.loc[(D2D_group['class'] == class_) & (D2D_group['HL'])])

        for header in groups_in_class['Header']:
            # Choose 2 devices to initiate RA procedure
            members_in_group = D2D_member.loc[(
                D2D_member.Header == header) & (D2D_member.response)]
            if not len(members_in_group):
                continue
            chosen_device_0 = members_in_group['transmit'].idxmax()
            devices_list.append(chosen_device_0)
            members_in_group = members_in_group.drop(chosen_device_0)
            chosen_device_1 = members_in_group['transmit'].idxmax()
            devices_list.append(chosen_device_1)

    elif TDCR == 'H':  # Heavy loading TDCR frame
        for class_ in class_list:
            groups_in_class = groups_in_class.append(
                D2D_group.loc[(D2D_group['class'] == class_) & (D2D_group['HL'])])

        for header in groups_in_class['Header']:
            # Choose 1 device to initiate RA procedure
            members_in_group = D2D_member.loc[(
                D2D_member.Header == header) & (D2D_member.response)]
            if not len(members_in_group):
                continue
            chosen_device_0 = members_in_group['transmit'].idxmax()
            devices_list.append(chosen_device_0)

    # Random Access compete
    if len(devices_list) != 0:
        framePreambles = [[] for _ in range(N_preamble)]
        for device_id in devices_list:
            framePreambles[random.randrange(N_preamble)].append(device_id)
        for preamble in range(N_preamble):
            devices = framePreambles[preamble]
            if len(devices) == 0:  # empty preamble
                continue
            if len(devices) == 1:  # success preamble
                N_Success += 1
                nMTCD_success += 1
                device_id = framePreambles[preamble][0]
                header_id = D2D_member.at[device_id, 'Header']
                D2D_group.loc[D2D_group['Header'] == header_id, 'N_RA'] -= 1
                RA_data.at[device_id, 'RA_success'] = frame
                RA_data.at[device_id, 'RA_transmit'] += 1
                D2D_member.at[device_id, 'request'] = False
                D2D_member.at[device_id, 'response'] = False

            else:  # collided preamble
                N_Collided += 1
                RA_data.at[device_id, 'RA_transmit'] += 1
                if RA_data.at[device_id, 'RA_transmit'] >= maxTrans:
                    nMTCD_fail += 1
                    D2D_member.at[device_id, 'request'] = False
                    D2D_member.at[device_id, 'response'] = False
        N_RA = len(devices_list)

    # update class information in BS
    for class_ in class_list:
        N_HL = len(
            D2D_group.loc[(D2D_group['class'] == class_) & (D2D_group['HL'])])
        if N_HL >= 38:
            Class_Status[class_] = 'H'
        elif N_HL >= 27:
            Class_Status[class_] = 'M'
        else:
            Class_Status[class_] = 'N'

    # update RA_result
    RA_result = RA_result.append(
        {'TDCR': TDCR, 'N_RA': N_RA,
         'empty': N_preamble - (N_Success + N_Collided),
         'collided': N_Collided, 'success': N_Success}, ignore_index=True)

    if nMTCD_success + nMTCD_fail >= nMTCD:
        break
    print(f'Simulation {nMTCD} Frame: {frame}')
    print(f'Simulation {nMTCD} Time Spent: ', time.time() - start_time)

print(
    f'Simulation TDCR of {nMTCD} devices ends in: {frame}', time.time() - start_time)

D2D_data = D2D_member[['Header', 'success', 'transmit']]
D2D_data.columns = ['Header', 'D2D_success', 'D2D_transmit']

Device_result = pd.concat([D2D_data, RA_data], axis=1, sort=False)
Device_result.to_csv(f'result/D2D_basic_Device_Result_{nMTCD}.csv', index=False)

D2D_result.to_csv(f'result/D2D_basic_D2D_Result_{nMTCD}.csv', index=False)

RA_result.to_csv(f'result/D2D_basic_RA_Result_{nMTCD}.csv', index=False)
