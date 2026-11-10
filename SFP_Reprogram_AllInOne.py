#! /usr/bin/env python3
# All-in-one: unlock an FS SFP and rewrite its part-number string, in one pass.
#
# It performs the full, verified procedure FS specified:
#   1. (optionally) wait for a fresh module insertion, then settle 500 ms
#      after power-up before touching the password  (FS requirement);
#   2. read the module serial from the EEPROM and look up its password
#      (passwords are per-module, grouped by serial — see sfp_passwords.txt);
#   3. back up the current A0h page to backup/ before changing anything;
#   4. write the 4-byte password to A2h (0x51) register 0x7B (no page-select
#      or enable register is needed);
#   5. confirm the EEPROM is now writable with a harmless canary byte;
#   6. write the new part number to A0h 0x28..0x37 (padded to 16 bytes),
#      recompute CC_BASE (checksum of bytes 0..62) and write it to 0x3F;
#   7. read everything back and verify.
#
# The unlock lasts only until the module is powered down, so the whole thing
# runs in a single power cycle. Nothing destructive happens unless the canary
# test confirms the module actually unlocked.
#
# Passwords live in sfp_passwords.txt (git-ignored) — never hard-coded here,
# because this repo is public.
#
# Usage:
#   ./SFP_Reprogram_AllInOne.py                       # PN=PS-FB-TX1310, auto password
#   ./SFP_Reprogram_AllInOne.py --pn PS-FB-RX1310
#   ./SFP_Reprogram_AllInOne.py --wait-insert         # wait for you to (re)plug it
#   ./SFP_Reprogram_AllInOne.py --password F0517AB7   # override the lookup
#   ./SFP_Reprogram_AllInOne.py --dry-run             # unlock + canary test only

import sys, os, time, argparse
try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus

I2C_BUS = 1
A0 = 0x50            # identification page
A2 = 0x51            # page carrying the password-entry RAM
PW_REG = 0x7b        # password: 4 bytes from 0x7B
PN_REG = 0x28        # vendor part number: 16 bytes 0x28..0x37
SN_REG = 0x44        # vendor serial number: 16 bytes 0x44..0x53
CC_REG = 0x3f        # CC_BASE: checksum of bytes 0..62
CANARY = 0x35        # a PN padding space (0x20) — harmless to poke
SETTLE_S = 0.5       # FS: wait 500 ms after power-up before the password

HERE = os.path.dirname(os.path.abspath(__file__))

def load_passwords(path):
    pw = {}
    if not os.path.exists(path):
        return pw
    for line in open(path):
        line = line.split('#', 1)[0].strip()
        if ':' in line:
            sn, val = line.split(':', 1)
            pw[sn.strip()] = val.strip()
    return pw

def parse_pw(s):
    s = s.replace(' ', '').replace('0x', '').replace('0X', '')
    if len(s) != 8:
        sys.exit("password must be 8 hex digits, e.g. F0517AB7")
    return [int(s[i:i+2], 16) for i in range(0, 8, 2)]

def present(bus):
    try:
        bus.read_byte_data(A0, 0); return True
    except OSError:
        return False

def read_str(bus, reg, n):
    return ''.join(chr(bus.read_byte_data(A0, reg + i)) for i in range(n))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pn', default='PS-FB-TX1310', help='target part number (<=16 chars)')
    ap.add_argument('--password', help='override: 8 hex digits')
    ap.add_argument('--pwfile', default=os.path.join(HERE, 'sfp_passwords.txt'))
    ap.add_argument('--wait-insert', action='store_true',
                    help='wait for the module to be removed and re-inserted first')
    ap.add_argument('--dry-run', action='store_true',
                    help='unlock and canary-test only; do not change the part number')
    args = ap.parse_args()

    target = args.pn
    if len(target) > 16:
        sys.exit("part number too long (max 16 bytes): %r" % target)
    pn = (target + ' ' * 16)[:16]

    with SMBus(I2C_BUS) as bus:
        # 1. power-up timing
        if args.wait_insert:
            if present(bus):
                print(">>> Please UNPLUG the module ...")
                while present(bus): time.sleep(0.05)
            print(">>> Now PLUG IT BACK IN ...")
            while not present(bus): time.sleep(0.01)
        if not present(bus):
            sys.exit("no module detected on i2c-%d 0x50" % I2C_BUS)
        print("Module detected; waiting %.0f ms after power-up ..." % (SETTLE_S * 1000))
        time.sleep(SETTLE_S)

        # 2. identify and pick password
        serial = read_str(bus, SN_REG, 16).strip()
        cur_pn = read_str(bus, PN_REG, 16)
        print("Serial = %r   current PN = %r" % (serial, cur_pn))
        if args.password:
            pw = parse_pw(args.password); src = "command line"
        else:
            table = load_passwords(args.pwfile)
            if serial not in table:
                sys.exit("no password for serial %r in %s — pass --password" %
                         (serial, args.pwfile))
            pw = parse_pw(table[serial]); src = os.path.basename(args.pwfile)
        print("Password source: %s" % src)

        # 3. backup A0h before any change
        os.makedirs(os.path.join(HERE, 'backup'), exist_ok=True)
        dump = bytes(bus.read_byte_data(A0, i) for i in range(256))
        ts = time.strftime("%Y%m%d_%H%M%S")
        bpath = os.path.join(HERE, 'backup', "sfp_0x50_%s_%s.bin" % (serial or 'unknown', ts))
        open(bpath, 'wb').write(dump)
        print("Backed up A0h -> %s" % bpath)

        # 4. write password (block write, within the 8-byte-per-write limit)
        bus.write_i2c_block_data(A2, PW_REG, pw)
        time.sleep(0.3)

        # 5. confirm unlock with the canary
        orig = bus.read_byte_data(A0, CANARY)
        test = 0x5a if orig != 0x5a else 0x4b
        bus.write_byte_data(A0, CANARY, test); time.sleep(0.2)
        unlocked = (bus.read_byte_data(A0, CANARY) == test)
        if bus.read_byte_data(A0, CANARY) != orig:
            bus.write_byte_data(A0, CANARY, orig); time.sleep(0.2)
        if not unlocked:
            sys.exit("UNLOCK FAILED — module still write-protected "
                     "(wrong password for this serial, or re-seat and retry). "
                     "No changes were made.")
        print("*** UNLOCKED ***")
        if args.dry_run:
            print("dry-run: leaving part number unchanged.")
            return 0

        # 6. write new part number + recompute checksum
        for i, ch in enumerate(pn):
            bus.write_byte_data(A0, PN_REG + i, ord(ch)); time.sleep(0.1)
        checksum = sum(bus.read_byte_data(A0, a) for a in range(0, 63)) & 0xff
        bus.write_byte_data(A0, CC_REG, checksum); time.sleep(0.15)

        # 7. verify
        new_pn = read_str(bus, PN_REG, 16)
        cc = bus.read_byte_data(A0, CC_REG)
        recalc = sum(bus.read_byte_data(A0, a) for a in range(0, 63)) & 0xff

    print("\nNew PN   = %r" % new_pn)
    print("CC_BASE  = 0x%02x (recalc 0x%02x) %s" %
          (cc, recalc, "OK" if cc == recalc else "MISMATCH"))
    ok = (new_pn == pn and cc == recalc)
    print("RESULT: %s" % ("*** PART NUMBER UPDATED ***" if ok else "FAILED — check module"))
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
