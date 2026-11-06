#! /usr/bin/env python3
# I2C access to the SFP EEPROM via the Linux kernel i2c-dev driver.
# Uses smbus2 (pure Python) or the system smbus module; no wiringPi needed,
# so it works on Raspberry Pi 3/4/5 regardless of /proc/cpuinfo contents.
try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus
import time

# I2C bus number: /dev/i2c-1 is the header pins (GPIO2=SDA, GPIO3=SCL)
# on all Raspberry Pi models since the Model B rev 2.
I2C_BUS = 1

#This function is used to read data from eeprom of SFP transicivers
#It uses IIC
def SFP_Read(dev_addr, start_reg_addr, read_len):
    data_str = ''
    with SMBus(I2C_BUS) as bus:
        for read_num in range(read_len):
            tmp = bus.read_byte_data(dev_addr, start_reg_addr + read_num)
            data_str = data_str + chr(tmp)
    return data_str

#This function is used to write data to eerpom of SFP transicivers
def SFP_Write(dev_addr,start_reg_addr, pn_name):
    with SMBus(I2C_BUS) as bus:
        for write_addr, tmp in enumerate(pn_name):
            bus.write_byte_data(dev_addr, start_reg_addr + write_addr, ord(tmp))
            time.sleep(0.1)
    checksum = SFP_Checksum(dev_addr)
    SFP_WriteChecksum(dev_addr,checksum)

#This function is used to cal checksum
def SFP_Checksum(dev_addr):
    sum = 0
    with SMBus(I2C_BUS) as bus:
        for addr in range(0,63):
            sum = sum + bus.read_byte_data(dev_addr, addr)
    checksum = sum&0xff
    print('checksum=0x%x'%(checksum))
    return (checksum)

#This function is used to write checksum
def SFP_WriteChecksum(dev_addr, checksum):
    with SMBus(I2C_BUS) as bus:
        bus.write_byte_data(dev_addr, 63, checksum)
    time.sleep(0.1)
