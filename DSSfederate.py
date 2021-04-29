import os
import datetime as dt
import pandas as pd
import helics as h
import json
from opendss_wrapper import OpenDSS

# Folder and File locations
MainDir = os.path.abspath(os.path.dirname(__file__))
ModelDir = os.path.join(MainDir, 'network_model')
ResultsDir = os.path.join(MainDir, 'results')
os.makedirs(ResultsDir, exist_ok=True)

# Output files
load_info_file = os.path.join(ResultsDir, 'load_info.csv')
main_results_file = os.path.join(ResultsDir, 'main_results.csv')
voltage_file = os.path.join(ResultsDir, 'voltage_results.csv')
elements_file = os.path.join(ResultsDir, 'element_results.csv')

# Create federate
fed = h.helicsCreateCombinationFederateFromConfig(
    os.path.join(os.path.dirname(__file__), "DSSfederate.json")
)

# register subscriptions
sub_pv_powers = h.helicsFederateRegisterSubscription(fed, "pv_powers", "")
sub_storage_powers = h.helicsFederateRegisterSubscription(fed, "storage_powers", "")

""" Create DSS Network """

MasterFile = os.path.join(ModelDir, 'Master.dss')
pv_dssfile = os.path.join(ModelDir, 'PVsystems.dss')
storage_dssfile = os.path.join(ModelDir, 'BatteryStorage.dss')
start_time = dt.datetime(2021, 1, 1)
stepsize = dt.timedelta(minutes=1)
duration = dt.timedelta(days=1)
dss = OpenDSS([MasterFile, pv_dssfile, storage_dssfile], stepsize, start_time)

# Run additional OpenDSS commands
dss.run_command('set controlmode=time')

# Get info on all properties of a class
df = dss.get_all_elements('Load')
df.to_csv(load_info_file)

""" Execute Federate, set up and start co-simulation """
h.helicsFederateEnterExecutingMode(fed)
main_results = []
voltage_results = []
element_results = []
times = pd.date_range(start_time, freq=stepsize, end=start_time + duration)
for step, current_time in enumerate(times):

    # Update time in co-simulation
    present_step = (current_time - start_time).total_seconds()
    present_step += 1  # Ensures other federates update before DSS federate
    h.helicsFederateRequestTime(fed, present_step)

    # get signals from other federate
    isupdated = h.helicsInputIsUpdated(sub_pv_powers)
    if isupdated == 1:
        pv_powers = h.helicsInputGetString(sub_pv_powers)
        pv_powers = json.loads(pv_powers)
    else:
        pv_powers = {}

    print(f"Current time: {current_time}, step: {step}. Received value: pv_powers = {pv_powers}")

    isupdated = h.helicsInputIsUpdated(sub_storage_powers)
    if isupdated == 1:
        storage_powers = h.helicsInputGetString(sub_storage_powers)
        storage_powers = json.loads(storage_powers)
    else:
        storage_powers = {}

    print(f"Current time: {current_time}, step: {step}. Received value: storage_powers = {storage_powers}")

    # set pv, storage powers
    for pv_name, set_point in pv_powers.items():
        dss.set_power(pv_name, element='Generator', p=set_point)

    for storage_name, set_point in storage_powers.items():
        dss.set_power(storage_name, element='Storage', p=set_point)

    # solve OpenDSS network model
    dss.run_dss()

    """ Get outputs for the feeder, all voltages, and individual element voltage and power """
    main_results.append(dss.get_circuit_info())

    voltage_results.append(dss.get_all_bus_voltages(average=True))

    element_results.append({
        'PV Power (kW)': dss.get_power('pv2', element='Generator', total=True)[0],
        'Storage Power (kW)': dss.get_power('battery2', element='Storage', total=True)[0],
        'Line Power (kW)': dss.get_power('L15', element='Line', line_bus=1)[0],
        'Load Power (kW)': dss.get_power('S10a', element='Load', total=True)[0],
        'Load Power (kVAR)': dss.get_power('S10a', element='Load', total=True)[1],
        'PV Voltage (p.u.)': dss.get_voltage('pv2', element='Generator', average=True),
        'Storage Voltage (p.u.)': dss.get_voltage('battery2', element='Storage', average=True),
        'Line Voltage (p.u.)': dss.get_voltage('L15', element='Line', average=True),
        'Load Voltage (p.u.)': dss.get_voltage('S10a', element='Load', average=True),
    })

""" Save results files """
pd.DataFrame(main_results).to_csv(main_results_file)
pd.DataFrame(voltage_results).to_csv(voltage_file)
pd.DataFrame(element_results).to_csv(elements_file)

# finalize and close the federate
h.helicsFederateFinalize(fed)
h.helicsFederateFree(fed)
h.helicsCloseLibrary()
