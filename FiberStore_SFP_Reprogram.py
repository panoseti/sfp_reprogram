#! /usr/bin/python
from SFP_WR_V1_1 import *

dev_addr = 0x50
start_reg_addr = 0x28
read_len = 16

data_str = SFP_Read(dev_addr, start_reg_addr, read_len)
print(data_str)

SFP0 = 'PS-FB-TX1310'
SFP1 = 'PS-FB-RX1310'

print('Please select SFP Part Number to be written:')
print('0--PS-FB-TX1310(TX:1310nm)')
print('1--PS-FB-RX1310(RX:1310nm)')
print('2--Other')
sfp_sel = input('Make your choice(0 or 1 or 2):')
sfp_sel = int(sfp_sel)

if sfp_sel == 0:
    SFP_PN = SFP0
elif sfp_sel == 1:
    SFP_PN = SFP1
elif sfp_sel == 2:
    SFP_PN = raw_input('Type in your Part Number:')
    print(SFP_PN)
else:
    print('You made a mistake,so we will use a default value--0')
    SFP_PN = SFP0

sfp_len = len(SFP_PN)
if sfp_len>16:
    print('length of PartNumber out of range, it should be less thant 16 bytes')
    print('We will use the default Part Number--AXGE-1254-0531(TX:1310nm)')
    SFP_PN = SFP0
    
for i in range(16-sfp_len):
    SFP_PN = SFP_PN + ' '

print('The part number will be written is %s'% SFP_PN)
SFP_Write(dev_addr, start_reg_addr, SFP_PN)

data_str = SFP_Read(dev_addr, start_reg_addr, read_len)
print('SFP Part Number read back from eeprom:%s' % data_str)



