#! /usr/bin/python
import wiringpi as wpi
import time

#This function is used to read data from eeprom of SFP transicivers
#It uses IIC
def SFP_Read(dev_addr, start_reg_addr, read_len):
    ds = wpi.wiringPiI2CSetup(dev_addr)
    read_num = 0
    data_str = ''
    while read_num != read_len:
        tmp = wpi.wiringPiI2CReadReg8(ds,start_reg_addr + read_num)
        read_num = read_num + 1
        data_str = data_str + chr(tmp)
    return data_str

#This function is used to write data to eerpom of SFP transicivers
def SFP_Write(dev_addr,start_reg_addr, pn_name):
    ds = wpi.wiringPiI2CSetup(dev_addr)
    write_addr = 0
    for tmp in list(pn_name):
        ans = wpi.wiringPiI2CWriteReg8(ds,start_reg_addr + write_addr,ord(tmp))
        write_addr = write_addr + 1
        time.sleep(0.1)
    checksum = SFP_Checksum(dev_addr)
    SFP_WriteChecksum(dev_addr,checksum)

#This function is used to cal checksum
def SFP_Checksum(dev_addr):
    sum = 0
    data = 0
    ds = wpi.wiringPiI2CSetup(dev_addr)
    for addr in range(0,63):
	data = wpi.wiringPiI2CReadReg8(ds,addr)
	sum = sum + data
    checksum = sum&0xff
    print('checksum=0x%x'%(checksum))
    return (checksum)

#This function is used to write checksum
def SFP_WriteChecksum(dev_addr, checksum):
    ds = wpi.wiringPiI2CSetup(dev_addr)
    ans = wpi.wiringPiI2CWriteReg8(ds,63,checksum)
    time.sleep(0.1)