# How to use the py script?
1. clone the repository to your Raspberry Pi
    ```
        git clone https://github.com/panoseti/sfp_reprogram.git
    ```
2. enable IIC interface on your Raspberry Pi:
    ```
        sudo raspi-config
    ```
    Then select "Interface Options-->I5 I2C-->Yes!"  
3. install smbus2 (wiringpi is no longer needed; it fails on Pi 4/5 with
   "Unable to determine board revision")  
    ```
        sudo apt install python3-smbus2
    ```  
    or `pip install smbus2`. Check the transceiver is detected (should show `50`):
    ```
        sudo apt install i2c-tools
        i2cdetect -y 1
    ```  
4. run "FiberStore_SFP_Reprogram.py"  
    ```
        ./FiberStore_SFP_Reprogram.py
    ```


