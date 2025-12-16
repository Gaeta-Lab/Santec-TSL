import socket
import logging

class SantecTSL:
    def __init__(self, host, port, timeout=5) -> None:
        self.conn = socket.create_connection((host, port), timeout=timeout)
        logging.info('Connection opened')
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
        logging.info('Connection closed')

    def __del__(self):
        self.conn.close()
        logging.info('Connection closed')

    def _write(self, msg) -> None:
        if not isinstance(msg, bytes):
            msg = bytes(msg, 'UTF-8')
        if not msg.endswith(b'\r\n'):
            msg += b'\r\n'
        self.conn.sendall(msg)

    def _read(self, terminator='\r'):
        response = ''
        while True:
            response += self.conn.recv(1024).decode()
            if response.endswith(terminator):
                break
        return response

    def _query(self, query):
        self._write(query)
        return self._read()

    def set_start_wavelength(self, wavelength: float) -> None:
        '''Set sweep start wavelength in nm
        
        wavelength: target wavelength in nm (0.1 pm precision)

        It will fail silently if wavelength is outside of range
        '''
        _str = f':WAV:SWE:STAR {wavelength:4.4f}\r\n'
        self._write(_str.encode())

    def read_start_wavelength(self) -> float:
        '''Set sweep start wavelength in nm'''
        return float(self._query(':WAV:SWE:STAR?'))

    def set_stop_wavelength(self, wavelength: float) -> None:
        '''Set sweep stop wavelength in nm

        wavelength: target wavelength in nm (0.1 pm precision)

        It will fail silently if wavelength is outside of range
        '''
        _str = f':WAV:SWE:STOP {wavelength:4.4f}\r\n'
        self._write(_str.encode())

    def read_stop_wavelength(self) -> float:
        '''Set sweep stop wavelength in nm'''
        return float(self._query(':WAV:SWE:STOP?'))

    def set_sweep_speed(self, speed: float) -> None:
        '''Set sweep speed in nm/s

        Valid speeds:
            1,2,5,10,20,50,100,200 (nm/s)
        '''
        _str = f':WAV:SWE:SPE {speed:.0f}\r\n'
        self._write(_str)

    def read_sweep_speed(self) -> float:
        '''Read sweep speed in nm/s'''
        return float(self._query(':WAV:SWE:SPE?'))

    def set_sweep_cycles(self, count: int) -> None:
        '''Set number of times laser sweeps'''
        if not isinstance(count, int):
            self.conn.close()
            raise ValueError('Sweep cycles requires an int')
        _str = f':WAV:SWE:CYCL {count}\r\n'
        self._write(_str.encode())

    def read_sweep_cycles(self) -> int:
        '''Read number of times laser sweeps'''
        return int(self._query(':WAV:SWE:CYCL?'))

    def set_sweep_delay(self, delay: int | float) -> None:
        '''Sets time between sweeps if continuous sweep is being used'''
        if not isinstance(delay, (int, float)):
            self.conn.close()
            raise ValueError('Delay requires an int or float')
        _str = f':WAV:SWE:DEL {delay:.1f}\r\n'
        self._write(_str.encode())

    def read_sweep_delay(self) -> float:
        '''Read delay between sweeps

        Returns:
            (float): delay in seconds
        '''
        return float(self._query(':WAV:SWE:DEL?'))

    def read_sweep_status(self) -> int:
        '''Reads sweep status

        The laser response will be one of these:
            + 0: Stopped
            + 1: Running
            + 3: Standing by trigger
            + 4: Preparation for sweep start

        Returns:
            (int): See list above
        '''
        return int(self._query(':WAV:SWE?'))

    def read_sweep_dwell(self) -> float:
        '''Reads time between steps if stepped sweep is being used'''
        return float(self._query(':WAV:SWE:DWEL?'))

    def read_sweep_mode(self) -> int:
        '''Reads sweep mode
        
        The laser response will be one of these:
            + 0: Step sweep mode and One way  
            + 1: Continuous sweep mode and One way
            + 2: Step sweep mode and Two way
            + 3: Continuous sweep mode and Two way

        Returns:
            (int): See list above
        '''
        return int(self._query(':WAV:SWE:MOD?'))

    def set_output_state(self, state: bool) -> None:
        '''Turn the laser output on or off

        Args:
            state (bool): True -> turn it on, False -> turn it off
        '''
        self._write(f':POW:STAT {1 if state else 0}')

    def read_output_state(self) -> bool:
        '''Is laser output is on?

        Returns:
            (bool): True if on, False if off
        '''
        return ( int(self._query(':POW:STAT?')) == 1 )

    def read_power_units(self) -> str:
        '''Get power units
        
        Returns:
            (str): `dBm` or `mW`
        '''
        unit = int(self._query(':POW:UNIT?'))
        if unit == 0:
            return 'dBm'
        return 'mW'

    def read_power(self) -> float:
        '''Get units with `read_power_units`'''
        return float(self._query(':POW?'))

    def read_power_actual(self) -> float:
        '''Reads power from builtin power meter

        Get units with `read_power_units`
        '''
        return float(self._query(':POW:ACT?'))

    def set_wavelength(self, wavelength: int | float) -> None:
        if not isinstance(wavelength, (int, float)):
            self.conn.close()
            raise ValueError('Wavelength requires an int or float')
        _str = f':WAV {wavelength:.4f}\r\n'
        self._write(_str)

    def read_wavelength(self) -> None:
        return float(self._query(':WAV?'))

    def start_sweep(self) -> None:
        self._write(b':WAV:SWE:STAT 1\r\n')

    def stop_sweep(self) -> None:
        self._write(b':WAV:SWE:STAT 0\r\n')

if __name__ == '__main__':
    from time import sleep
    santec = SantecTSL('192.168.0.11', '5000')
    cycles = santec.read_sweep_cycles()
    santec.set_wavelength(1300)
    sleep(1)
    print(santec.read_sweep_delay())
    print(santec.read_wavelength())
