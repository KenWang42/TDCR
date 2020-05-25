import pandas as pd
import numpy as np
import random
import os
import time

start_time = time.time()

path = os.path.abspath('.')

simRAO = 1000

nMTCD = 30000

nMTCD_success = 0  # total number of device that transmit success

nMTCD_fail = 0  # total number of device that transmit failed

Backoff = 2  # Backoff Indicator = 20ms

maxTrans = 10  # Maximum number of preamble transmission

N_PRB = 25  # Number of Sidelink Physical Resource Block

N_PRB_arrange = 20  # the number of arranged PRB

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
        RA_success:  Integer,
                     frame the device complete RA procedure
        RA_transmit: Integer,
                     number of the device trying to send RA request
"""
RA_data = MTCD_data[['RA_init', 'RA_success', 'RA_transmit']]

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
    Columns 4:
        Header:     Integer,
                    device_id of the group Header
        class:      Integer,
                    the barring class of the beloneing D2D group
        N_member:   Integer,
                    the total number of device (member+header) in the group
        arr_seq:    Integer,
                    current arrange sequence
"""
D2D_group = pd.DataFrame(
    columns=['Header', 'class', 'N_member', 'arr_seq']
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

# initialize current arrange sequence
D2D_group['arr_seq'] = np.zeros(N_group, dtype=int)


"""
BS_schedule
    indicate the broadcast information for SIB2
    update every 16 system frame
    Do not require initialize
    Index:
        system_frame
    Columns 1:
        class: Integer,
               the class can initiate RA procedure
"""
BS_schedule = pd.DataFrame(
    columns=['class'],
)

"""
D2D_result
    records the numerical result of D2D sidelink
    Index:
        sequence of SC-Period
    Columns 3:
         frame: Integer,
                the system frame when the SC-period-1 ends
         N_request: Integer,
                    number of device send D2D_request to its header
         N_response: Integer,
                    number of D2D device that receive its Header response
"""
D2D_result = pd.DataFrame(
    columns=['frame', 'N_request', 'N_response'],
)

# initialize class
BS_schedule['class'] = [f % N_class for f in range(simRAO)]

D2D_period = 8  # 40 ms Member -> Header, 40ms Header -> Member

SIB2_period = 16  # broadcast period of SIB2: 160ms

for frame in range(simRAO):
    # generate D2D request
    devices = RA_data.loc[(RA_data['RA_init'] == frame)
                          & (RA_data['RA_success'] == -1)]

    D2D_member.loc[devices.index, 'request'] = True
    D2D_member.loc[devices.index, 'response'] = False

    if frame % (D2D_period) == 4:
        members_ = D2D_member.loc[D2D_member.request].copy()
        N_D2D_request = len(members_)
        N_D2D_response = 0
        headers = members_['Header'].unique()
        for header in headers:
            # Members' request
            group_id = D2D_group.loc[D2D_group['Header'] == header].index[0]

            cur_arrange = D2D_group.at[group_id, 'arr_seq']

            group_members = members_.loc[(members_.Header == header)]

            arr_members = group_members.loc[group_members.arrange ==
                                            cur_arrange].index

            non_arr_members = group_members.loc[group_members.index.difference(
                arr_members)].index

            framePRB = [[] for _ in range(N_PRB)]

            for arr_member in arr_members:
                # compete arranged-PRB
                framePRB[random.randrange(N_PRB_arrange)].append(arr_member)
                D2D_member.at[arr_member, 'transmit'] += 1

            for non_arr_member in non_arr_members:
                if non_arr_member == header:  # header itself
                    D2D_member.at[header, 'response'] = True
                else:  # compete non-arranged-PRB
                    framePRB[random.randrange(N_PRB_arrange, N_PRB)].append(
                        non_arr_member)
                D2D_member.at[non_arr_member, 'transmit'] += 1
            for PRB in range(N_PRB):
                # check for the D2D request
                PRB_members = framePRB[PRB]
                if len(PRB_members) == 1:  # D2D request success
                    member_id = PRB_members[0]
                    D2D_member.at[member_id, 'request'] = False
                    D2D_member.at[member_id, 'response'] = True
                    D2D_member.at[member_id, 'success'] = frame
                    N_D2D_response += 1

            # arrange PRB sequence
            D2D_group.at[group_id, 'arr_seq'] += 1
            max_arr = D2D_group.at[group_id, 'N_member'] // N_PRB_arrange
            if D2D_group.at[group_id, 'arr_seq'] > max_arr:
                D2D_group.at[group_id, 'arr_seq'] = 0

        D2D_result.loc[len(D2D_result)] = [
            frame, N_D2D_request, N_D2D_response]

    # RA Procedure
    class_ = BS_schedule.at[frame, 'class']
    groups_in_class = D2D_group.loc[D2D_group['class'] == class_]

    for header in groups_in_class['Header']:
        # Choose device to initiate RA procedure
        members_in_group = D2D_member.loc[(
            D2D_member.Header == header) & (D2D_member.response)]
        if not len(members_in_group):
            continue
        chosen_device = members_in_group['transmit'].idxmax()
        RA_data.at[chosen_device, 'RA_success'] = frame
        RA_data.at[chosen_device, 'RA_transmit'] += 1
        D2D_member.at[chosen_device, 'request'] = False
        D2D_member.at[chosen_device, 'response'] = False
        nMTCD_success += 1

    if nMTCD_success >= nMTCD:
        print(frame)
        break

D2D_data = D2D_member[['Header', 'success', 'transmit']]
D2D_data.columns = ['Header', 'D2D_success', 'D2D_transmit']

Device_result = pd.concat([D2D_data, RA_data], axis=1, sort=False)
Device_result.to_csv(f'result/D2D_Device_Result_{nMTCD}.csv', index=False)

D2D_result.to_csv(f'result/D2D_Access_Result_{nMTCD}.csv', index=False)

print(f'{nMTCD} devices D2D simulation: ', time.time() - start_time)
