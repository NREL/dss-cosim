import os
import helics as h
import datetime as dt
import pandas as pd
import json

# Folder and File locations
MainDir = os.path.abspath(os.path.dirname(__file__))
ModelDir = os.path.join(MainDir, 'network_model')

start_time = dt.datetime(2021, 1, 1)
stepsize = dt.timedelta(minutes=1)
duration = dt.timedelta(days=1)

fed = h.helicsCreateCombinationFederateFromConfig(
    os.path.join(os.path.dirname(__file__), "federate1.json")
)

# register publications
# global
pub_pv_powers = h.helicsFederateRegisterGlobalTypePublication(fed, "pv_powers", "String", "")
pub_storage_powers = h.helicsFederateRegisterGlobalTypePublication(fed, "storage_powers", "String", "")

# pv, storage ratings and profiles
pv_powers_rated = {'pv1': 10.0, 'pv2': 15.0, 'pv3': 20.0, 'pv4': 10.0, 'pv5': 50.0}  # pv rating
pv_profile = pd.read_csv(os.path.join(ModelDir, 'pv_profile.csv'), header=None).to_numpy()

storage_powers_rated = {'battery1': 10.0, 'battery2': 15.0, 'battery3': 20.0, 'battery4': 10.0,
                        'battery5': 15.0}  # storage rating
storage_profile = pd.read_csv(os.path.join(ModelDir, 'storage_profile.csv'), header=None).to_numpy()

h.helicsFederateEnterExecutingMode(fed)

times = pd.date_range(start_time, freq=stepsize, end=start_time + duration)
for step, current_time in enumerate(times):

    # Update time in co-simulation
    present_step = (current_time - start_time).total_seconds()
    h.helicsFederateRequestTime(fed, present_step)

    # select multiplier
    pv_mult = float(pv_profile[step])
    storage_mult = float(storage_profile[step])

    pv_powers = {k: v * pv_mult for k, v in pv_powers_rated.items()}
    print(pv_powers)

    storage_powers = {k: v * storage_mult for k, v in storage_powers_rated.items()}
    print(pv_powers)

    # publish to other federates

    h.helicsPublicationPublishString(pub_pv_powers, json.dumps(pv_powers))
    print(f"Current time: {current_time}, step: {step}. Sent value: pv_powers = {pv_powers}")

    h.helicsPublicationPublishString(pub_storage_powers, json.dumps(storage_powers))
    print(f"Current time: {current_time}, step: {step}. Sent value: storage_powers = {storage_powers}")

h.helicsFederateFinalize(fed)
h.helicsFederateFree(fed)
h.helicsCloseLibrary()
