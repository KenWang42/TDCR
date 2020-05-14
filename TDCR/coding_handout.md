# Coding Handout

###### tags: `TDCR`

## Preamble_status

records the status of PRACH Preamble in every system frame (10ms)

- Index

  system frame

- Columns

  - N_request: Integer

    number of device that initiate RA request

  - empty: Integer

    number of preamble choose by no one

  - collided: Integer

    number of preamble choose by multiple devices

  - success: Integer

    number of preamble choose by exactly 1 device

## RA_data

records RA parameter and simulation result of every device

the parameters required in enB <-> device communication

- Index

  device_id

- Columns 4

  - RA_init: Integer,

    next frame the device send RA request

  - RA_first: Integer,

    first frame the device send RA request

  - RA_success: Integer,

    frame the device complete RA procedure

  - RA_transmit: Integer,

    number of the device trying to send RA request

## D2D_member

records D2D parameter of every Member

also records numerical result for every Member

the parameter required in Member -> Header communication

- Index

  device_id

- Columns 6:

  - group: Integer,

    the belonging D2D group

    also indicate the group Header's device_id

  - Member: Boolean,

    whether the device is a Member

  - arrange: Integer,

    indicate the belonging arrange sequence

  - request: Boolean,

    whether the Member will send D2D request

  - delay: Integer,

  total delay of D2D transmission

  - transmit: Integer,

  number of the Member trying to send D2D request

## D2D_group

records D2D parameter of every Header

also records numerical result for every Header

records the parameter required by Header -> Member communication

- Index:

default sequence

- Columns 5:

  - Header: Integer,

    device_id of the group Header

  - class: Integer,

    the barring class of the belonging D2D group

  - N_member: Integer,

    the total number of member in the group

  - RA_request: Integer,

    number of RA_request within the group

  - arrange: Integer,

    current arrange sequence

  - HL: Boolean,

    whether the group holds more than 38 RA request or not

## BS_schedule

indicate the broadcast information for SIB2

update every 16 system frame

Do not require initialize

- Index:

system_frame

- Columns 2:

  - class: Integer,

  the class can initiate RA procedure

  - TDCR: Integer,

    the TDCR level of the frame

        0: no TDCR frame

        1: 1 TDCR frame in this period, 2 device per group initiate RA

        2: 2 TDCR frame in this period, 1 device per group initiate RA

## class_status

List[Integer]

records current status of each class stored in the BS

update after the class sends RA request

0: no TDCR frame

1: 1 TDCR frame in this period, 2 device per group initiate RA

2: 2 TDCR frame in this period, 1 device per group initiate RA
