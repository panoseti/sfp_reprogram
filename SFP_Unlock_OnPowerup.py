#! /usr/bin/env python3
# Write the EEPROM unlock password to an FS SFP *immediately after power-up*.
#
# Some SFP modules only accept the password-entry write in a short window right
# after the module powers up; once it has been running, writes to the password
# RAM are ignored and the EEPROM stays write-protected.  Since the module is fed
# by the SFP cage, "power-up" means physically re-seating it (or power-cycling
# the cage).  This script:
#   1. waits for the module to DISAPPEAR from the I2C bus (you pull it out),
#   2. polls fast for it to RE-APPEAR (you plug it back in),
#   3. writes the 4-byte password the instant it answers,
#   4. verifies with a harmless "canary" byte whether the EEPROM is now writable.
#
# It does NOT change the part number.  Once this reports UNLOCKED, run the normal
# reprogram script within the same power cycle (the unlock stays valid until the
# module is reset or powered down again).
#
# Usage:  ./SFP_Unlock_OnPowerup.py [PASSWORD_HEX]
#         PASSWORD_HEX is 8 hex digits, default F0051ABA.

import sys, time
try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus

I2C_BUS   = 1
A0_ADDR   = 0x50      # identification page
PW_ADDR   = 0x51      # A2h page carrying the password-entry RAM
PW_REG    = 0x7b      # bytes 0x7b-0x7e (123-126): 32-bit password
CANARY    = 0x35      # A0h padding byte (a space, 0x20) - harmless to poke

def parse_pw(s):
    s = s.replace(' ', '').replace('0x', '')
    if len(s) != 8:
        sys.exit("password must be 8 hex digits, e.g. F0051ABA")
    return [int(s[i:i+2], 16) for i in range(0, 8, 2)]

def present(bus):
    try:
        bus.read_byte_data(A0_ADDR, 0)
        return True
    except OSError:
        return False

def main():
    pw = parse_pw(sys.argv[1] if len(sys.argv) > 1 else "F0051ABA")
    print("password to write: %s" % ' '.join('%02X' % b for b in pw))

    with SMBus(I2C_BUS) as bus:
        # 1. wait for removal so we catch a genuine fresh power-up
        if present(bus):
            print(">>> Please UNPLUG the SFP module now ...")
            while present(bus):
                time.sleep(0.05)
        print(">>> Module removed. Now PLUG IT BACK IN — writing password on power-up.")

        # 2. tight poll for re-appearance, then write password ASAP
        while not present(bus):
            pass  # busy-wait for minimal latency
        t0 = time.time()
        for off, b in enumerate(pw):
            for _ in range(5):            # retry briefly; A2h may lag A0h by a few ms
                try:
                    bus.write_byte_data(PW_ADDR, PW_REG + off, b)
                    break
                except OSError:
                    time.sleep(0.002)
        dt = (time.time() - t0) * 1000
        print(">>> Module detected; password written in %.1f ms." % dt)

        # 3. verify with the canary (non-destructive)
        time.sleep(0.1)
        try:
            orig = bus.read_byte_data(A0_ADDR, CANARY)
        except OSError:
            orig = None
        test = 0x5a if orig != 0x5a else 0x4b
        bus.write_byte_data(A0_ADDR, CANARY, test)
        time.sleep(0.15)
        now = bus.read_byte_data(A0_ADDR, CANARY)
        unlocked = (now == test)
        if now != orig and orig is not None:      # restore whatever we changed
            bus.write_byte_data(A0_ADDR, CANARY, orig)
            time.sleep(0.15)

        print("\nRESULT: %s" % ("*** UNLOCKED *** — run the reprogram script now, "
                                 "same power cycle." if unlocked
                                 else "still LOCKED (canary 0x%02x unchanged)." % now))
        return 0 if unlocked else 1

if __name__ == "__main__":
    sys.exit(main())
