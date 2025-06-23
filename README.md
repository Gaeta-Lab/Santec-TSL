# Santec-TSL Python LAN Driver

This is a pretty incomplete python driver for communicating with a Santec TSL laser series laser over LAN. 

Example:
```python
from santec_tsl import SantecTSL

with SantecTSL('192.168.0.197', port='5000') as santec:
    print(santec.read_wavelength())
```
