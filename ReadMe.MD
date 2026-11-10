# FS SFP transceiver reprogramming

Scripts to rewrite the part-number (model) string stored in the EEPROM of
FiberStore (FS) SFP transceivers, driven over I2C from a Raspberry Pi.

## Setup

1. Clone the repository to your Raspberry Pi:
    ```
    git clone https://github.com/panoseti/sfp_reprogram.git
    ```
2. Enable the I2C interface:
    ```
    sudo raspi-config
    ```
    Then select "Interface Options --> I5 I2C --> Yes".
3. Install dependencies (wiringpi is no longer needed; it fails on Pi 4/5 with
   "Unable to determine board revision"):
    ```
    sudo apt install python3-smbus2 i2c-tools
    ```
    or `pip install smbus2`. Check the transceiver is detected (0x50, and
    usually 0x51 for diagnostics):
    ```
    i2cdetect -y 1
    ```

## Quick start (recommended)

`SFP_Reprogram_AllInOne.py` does the whole thing — unlock, rewrite, checksum,
verify — in one pass, after you set up the password file below:

```
./SFP_Reprogram_AllInOne.py --pn PS-FB-TX1310
```

Useful flags: `--wait-insert` (wait for you to re-seat the module first),
`--password XXXXXXXX` (override the lookup), `--dry-run` (unlock + test only,
no change). It auto-reads the module serial, looks up its password, backs up
the A0h page to `backup/`, and only changes anything after the unlock is
confirmed.

`FiberStore_SFP_Reprogram.py` is the original interactive script (prompts for a
part number). It only works if the module is **not** write-protected, or if you
have already unlocked it in the same power cycle.

## Newer modules are write-protected (important)

Modules from recent batches ship with the A0h EEPROM **write-protected**: I2C
write commands are ACKed but the bytes do not change. You must enter a password
first. Symptoms, if you skip this: the reprogram script runs without error but
the part number reads back unchanged.

### Unlock procedure (confirmed with FS)

- **Password is per-module**, tied to the serial number — different modules in
  the same order can have different passwords. Get them from FS (quote your
  order number and the module serials).
- **Where:** write **4 bytes** to page **A2h (I2C address 0x51), register 0x7B**
  (0x7B..0x7E). No page-select or enable register is needed first.
- **Timing:** wait **500 ms after module power-up** before writing the password.
- **Scope:** the unlock lasts only until the module loses power, so unlock and
  reprogram in the **same power cycle**.
- After unlocking, the part number (A0h 0x28..0x37, 16 bytes, space-padded) is
  written byte-by-byte, then **CC_BASE at 0x3F** (the checksum of bytes 0..62)
  must be recomputed — the helper scripts do this automatically.

### Password file (local, not committed)

Passwords are **not** stored in this repo (it is public). Put them in a local
file `sfp_passwords.txt` (git-ignored), one per line:

```
# <SERIAL>: <8-hex-digit password>
G2440848765: XXXXXXXX
```

`SFP_Reprogram_AllInOne.py` reads this file and matches on the serial it reads
from the module.

## Files

| File | Purpose |
|------|---------|
| `SFP_Reprogram_AllInOne.py` | Unlock + rewrite + checksum + verify, one pass (recommended) |
| `SFP_Unlock_OnPowerup.py`   | Just enter the password right after power-up (diagnostics) |
| `FiberStore_SFP_Reprogram.py` | Original interactive reprogram (needs an unlocked module) |
| `SFP_WR_V1_1.py`            | Low-level I2C read/write/checksum helpers (smbus2) |
| `sfp_passwords.txt`         | **Local only, git-ignored** — your FS passwords |
| `backup/`                   | **Local only, git-ignored** — EEPROM backups |

## Backups

The all-in-one script backs up the A0h page automatically before writing. To
back up manually at any time:

```
i2cdump -y 1 0x50 b > backup/sfp_0x50_manual.txt
```

Keep a backup before reprogramming — it lets you restore the original identity.
