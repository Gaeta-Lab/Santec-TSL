import telnetlib
import logging

class SantecTSL:
    def __init__(self, host, port, timeout=5) -> None:
        self.tn = telnetlib.Telnet(host=host, port=port, timeout=5)
        logging.info('Connection opened')
        #self.tn.read_until(b"\n")
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.tn.close()
        logging.info('Connection closed')

    def __del__(self):
        self.tn.close()
        logging.info('Connection closed')

    def _query(self, query):
        if not isinstance(query, bytes):
            query = bytes(query, 'UTF-8')
        if not query.endswith(b'\r\n'):
            query += b'\r\n'
        
        self.tn.write(query)
        return (self.tn.read_some()).decode()

    def read_start_wavelength(self) -> float:
        return float(self._query(':WAV:SWE:STAR?'))

    def read_stop_wavelength(self) -> float:
        return float(self._query(':WAV:SWE:STOP?'))

    def read_sweep_status(self) -> float:
        return float(self._query(':WAV:SWE?'))

    def read_sweep_speed(self) -> float:
        return float(self._query(':WAV:SWE:SPE?'))

    def read_sweep_dwell(self) -> float:
        '''Reads time between steps if stepped sweep is being used'''
        return float(self._query(':WAV:SWE:DWEL?'))

    def read_sweep_mode(self) -> int:
        '''Reads sweep mode
        
        Returns:
            0: Step sweep mode and One way
            1: Continuous sweep mode and One way
            2: Step sweep mode and Two way
            3: Continuous sweep mode and Two way
        '''
        return int(self._query(':WAV:SWE:MOD?'))

    def read_sweep_cycles(self) -> int:
        return int(self._query(':WAV:SWE:CYCL?'))

    def start_sweep(self) -> None:
        self.tn.write(b':WAV:SWE:STAT 1\r\n')

    def stop_sweep(self) -> None:
        self.tn.write(b':WAV:SWE:STAT 0\r\n')

    def set_sweep_cycles(self, count: int) -> None:
        if not isinstance(count, int):
            self.tn.close()
            raise ValueError('Sweep cycles requires an int')
        _str = f':WAV:SWE:CYCL {count}\r\n'
        self.tn.write(_str.encode())

    def set_sweep_delay(self, delay: int | float) -> None:
        '''Sets time between sweeps if continuous sweep is being used'''
        if not isinstance(delay, (int, float)):
            self.tn.close()
            raise ValueError('Delay requires an int or float')
        _str = f':WAV:SWE:DEL {delay:.1f}\r\n'
        self.tn.write(_str.encode())

    def set_wavelength(self, wavelength: int | float) -> None:
        if not isinstance(wavelength, (int, float)):
            self.tn.close()
            raise ValueError('Wavelength requires an int or float')
        _str = f':WAV {wavelength:.4f}nm\r\n'
        self.tn.write(_str.encode())

    def read_wavelength(self) -> None:
        return float(self._query(':WAV?'))


if __name__ == '__main__':
    from time import sleep
    santec = SantecTSL('192.168.0.200', '5000')
    cycles = santec.read_sweep_cycles()
    santec.set_wavelength(1638)
    sleep(1)
    print(santec.read_wavelength())
