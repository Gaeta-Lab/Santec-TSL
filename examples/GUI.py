import FreeSimpleGUI as sg
from santec_tsl import SantecTSL
import json

ip = '192.168.0.10'
port = '5000'

laser_status_lut = {
    0: 'Step sweep mode and One way',
    1: 'Continuous sweep mode and One way',
    2: 'Step sweep mode and Two way',
    3: 'Continuous sweep mode and Two way'
}

sweep_status_lut = {
    0: 'Stopped',
    1: 'Running',
    3: 'Standing by trigger',
    4: 'Preparation for sweep start'
}

laser_state = {
    'on': False,
    'power': 0,
    'power_unit': 'mW',
    'sweep_mode': 0,
    'wavelength': 0,
    'sweep_status': 0,
    'sweep_speed': 0,
    'sweep_start': 0,
    'sweep_stop': 0
}

def update_gui(on, power, power_unit, wavelength, sweep_mode, sweep_status, sweep_speed, sweep_start, sweep_stop):
    window['power'].update( 'ON' if on else 'OFF' )
    window['power level'].update(f'{power:.3f} {power_unit}')
    window['sweep mode'].update( f'\tMode: { sweep_mode }' )
    window['wavelength'].update(f'{wavelength:.4f} nm')
    window['sweep speed'].update(f'Speed: {sweep_speed} nm/s')
    window['sweep status'].update(sweep_status)
    window['sweep range'].update(f'\t{sweep_start:.2f}-{sweep_stop:.2f} nm')

def update(santec):
    laser_state['on'] = santec.read_output_state()
    laser_state['power'] = santec.read_power()
    laser_state['power_unit'] = santec.read_power_units()
    laser_state['wavelength'] = santec.read_wavelength()
    laser_state['sweep_mode'] = laser_status_lut[ santec.read_sweep_mode() ]
    laser_state['sweep_status'] = sweep_status_lut[ santec.read_sweep_status() ]
    laser_state['sweep_speed'] = santec.read_sweep_speed()
    laser_state['sweep_start'] = santec.read_start_wavelength()
    laser_state['sweep_stop'] = santec.read_stop_wavelength()
    update_gui(**laser_state)
    highlight_order()

def go_to(santec, wavelength):
    #if santec.read_sweep_status() != 0:
    santec.stop_sweep()
    santec.set_wavelength(wavelength)
    update(santec)

def start_sweep(santec):
    santec.start_sweep()
    update(santec)

font = ("Inconsolata", 20)
font_small = ("Inconsolata", 12)
helpstring = '''Press Control-z to toggle between text input mode and arrow key mode'''

sg.theme('BrightColors')

layout = [  
    [sg.Text("--", key='power'), sg.Text("", key='power level'), sg.Multiline("----.---- nm", disabled=True, size=(12, 1), no_scrollbar=True, key='wavelength')],
    [sg.Text("Sweep: "), sg.Text("", key='sweep status')],
    [sg.Text("\tMode: ", key='sweep mode')],
    [sg.Text("\t-", key='sweep range'), sg.Text("Speed: ", key='sweep speed')],
    [sg.Button('Toggle Power'), sg.Button('Start Sweep'), sg.Button('Update'), sg.Button('Exit')],
    [sg.Input(default_text='1550.000'), sg.Button('Go to')],
    [sg.Input(default_text='1637.000'), sg.Button('Set Start')],
    [sg.Input(default_text='1483.000'), sg.Button('Set Stop')],
    [sg.Input(default_text='santec_settings.json'), sg.Button('Export')],
    [sg.Input(default_text=ip, size=(15,1)), sg.Button('Set IP'), sg.Input(default_text=port, size=(5,1)), sg.Button('Set Port')],
    [sg.Text(helpstring, font=font_small)],
    [sg.Text('', key='error')]
]

window = sg.Window('SANTEC TSL', layout, font=font, finalize=True)

window.bind('<Control-z>', '+TOGGLEMOD+')
window.bind('<Up>', 'up')
window.bind('<Down>', 'down')
window.bind('<Left>', 'left')
window.bind('<Right>', 'right')

wavelength_text = window['wavelength'].Widget
wavelength_text.tag_config('highlight', background='lightgrey')

order = -4
def highlight_order():
    wavelength_text.tag_remove('highlight', '1.0', sg.tk.END)
    if order >= 0:
        wavelength_text.tag_add('highlight', f'1.{3 - order}', f'1.{4 - order}')
    else:
        wavelength_text.tag_add('highlight', f'1.{4 - order}', f'1.{5 - order}')
highlight_order()

def change_order(mod):
    global order
    order += mod
    if order < -4:
        order = -4
    if order > 2:
        order = 2
    highlight_order()

def adjust_wavelength(santec, mod):
    if santec.read_sweep_status() != 0:
        print('Laser sweeping, can\'t adjust wavelength')
        return
    wl = santec.read_wavelength()
    wl += mod * 10 ** order
    santec.set_wavelength(wl)

keyboard_mod = False

connection_commands = ['Toggle Power', 'Update', 'Start Sweep', 'Go to', 'Set Start', 'Set Stop', 'Export']

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    elif event == '+TOGGLEMOD+':
        keyboard_mod = not keyboard_mod
        if keyboard_mod:
            santec = SantecTSL(ip, port)
            wavelength_text.tag_config('highlight', background='pink')
        else:
            santec.close()
            wavelength_text.tag_config('highlight', background='lightgrey')

    if keyboard_mod:
        if event == 'left':
            change_order(1)
        elif event == 'right':
            change_order(-1)
        elif event == 'up':
            adjust_wavelength(santec, 1)
            update(santec)
        elif event == 'down':
            adjust_wavelength(santec, -1)
            update(santec)
    else:
        if event in connection_commands:
            try:
                santec = SantecTSL(ip, port, timeout=1)
            except (TimeoutError, OSError) as e:
                print('Unable to connect to Santec\nError:\n\t', e)
                window['error'].update(f'ERROR: Could not connect to Santec at {ip}:{port}')
            else:
                window['error'].update('')
                with santec:
                    if event == 'Toggle Power':
                        state = santec.read_output_state()
                        santec.set_output_state(not state)
                        update(santec)
                    elif event == 'Update':
                        update(santec)
                    elif event == 'Start Sweep':
                        start_sweep(santec)
                    elif event == 'Go to':
                        wavelength = float(values[0])
                        go_to(santec, wavelength)
                    elif event == 'Set Start':
                        wavelength = float(values[1])
                        santec.set_start_wavelength(wavelength)
                        update(santec)
                    elif event == 'Set Stop':
                        wavelength = float(values[2])
                        santec.set_stop_wavelength(wavelength)
                        update(santec)
                    elif event == 'Export':
                        update(santec)
                        fname = values[3]
                        with open(fname, 'w') as f:
                            json.dump(laser_state, f, indent=4)
        else:
            if event == 'Set IP':
                ip = values[4]
            elif event == 'Set Port':
                port = values[5]

window.close()
