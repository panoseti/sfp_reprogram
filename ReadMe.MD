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
3. install wiringpi  
    ```
        sudo pip install wiringpi
    ```  
4. run "FiberStore_SFP_Reprogram.py"  
    ```
        ./FiberStore_SFP_Reprogram.py
    ```


