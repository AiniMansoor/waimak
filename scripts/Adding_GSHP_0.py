""" 
This script is an example of how to use this repository.

- The goal is to import a MODFLOW model from GNS and use this to base your experiments on. 

The model is a MODFLOW-NWT model rather than a MODFLOW6 model, so the packages are a bit different than what you've seen before

So if you want to make some changes to a model, the procedure is as follows:
    - import the model using relevent function, import_gns_model()
    - (run it to make sure it's working)
    - add or change some packages (this will be the tricky park)
    - run it again
    - postprocess the results

"""

import os
import numpy as np
import matplotlib.pyplot as plt
import flopy_mh as flopy
from waimak_extended_boundry.model_run_tools.model_setup.base_modflow_wrapper import import_gns_model
from copy import deepcopy
from waimak_extended_boundry import smt
import pandas as pd


def import_model(name):
    """ import the gns model using the provided function, import_gns_model

        inputs:
            name: name that you want the model to have. 
    """

    workspace = os.path.join("flopy_data")
    if not os.path.exists(workspace):
        os.makedirs(workspace)

    # this is to pick which of the optimizations to use
    # if you want to try out some of the other ones, I can grab them for you
    # \.waimak\model\required\pre-stocastic_extended_models\README.txt for more details
    model_id = "NsmcBase" 
                        
    dir_path = os.path.join(os.getcwd(), workspace)

    m = import_gns_model(model_id, name, dir_path)
    m.write_input()
    return m

def load_model(name):
    """ load model that you have already imported from GNS
        
        inputs: 
            name: this is the name of the model NsmcBase_{name}
    """

    model_id = "NsmcBase" 
    model_name = model_id + "_" + name
    model_dir = os.path.join("flopy_data\{}".format(model_name))

    m = flopy.modflow.Modflow.load(model_name + ".nam", model_ws=model_dir)
    exe_name = os.path.join(os.getcwd(), r"model\required\models_exes\MODFLOW-NWT_1.1.2\MODFLOW-NWT_1.1.2\bin\MODFLOW-NWT.exe")
    m.exe_name = exe_name
    return m


def run_model(m):
    
    success, buff = m.run_model()
    if not success:
        raise Exception("MODFLOW did not terminate normally.")


def copy_model(m, name):
    """ copy the model. Useful if you want to incrementally change a model"""

    model_id = "NsmcBase" 
    model_name = model_id + "_" + name
    dir_path = os.path.join("flopy_data\{}".format(model_name))   

    m._set_name(model_name)
    m.change_model_ws(dir_path)

    # create output stuff
    units = deepcopy(m.output_units)
    for u in units:
        m.remove_output(unit=u)

    fnames = [m.name + e for e in ['.hds', '.ddn', '.cbc', '.sfo']]  # output extension
    funits = [30, 31, 740, 741]  # fortran unit
    fbinflag = [True, True, True, True, ]  # is binary
    fpackage = [[], [], ['UPW', 'DRN', 'RCH', 'SFR', 'WEL'], ['SFR']]
    for fn, fu, fb, fp, in zip(fnames, funits, fbinflag, fpackage):
        m.add_output(fn, fu, fb, fp)

    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    m.write_input()

    return m

def gshp_well_data():
    """Importing the flow, lon, lat, and elv of wells"""
    gshp_abs = pd.read_excel(r"model\well_data\abstraction_wells.xlsx")
    gshp_inj = pd.read_excel(r"model\well_data\injection_wells.xlsx")
    return gshp_abs, gshp_inj

def add_well(m, lon, lat, elv, q):
    """ add a well to a model, using NZTM and masl coordinates"""
    # finding location of the well
    lay, row, col = smt.convert_coords_to_matix(lon, lat, elv)

    # add row to wel array
    temp_wel_data = m.wel.stress_period_data.data[0]
    temp_wel_data.resize(temp_wel_data.shape[0], refcheck=False) # probably a better way to do this
    temp_wel_data[-1] = (lay, row, col, q)
    m.wel.stress_period_data.data[0] = temp_wel_data
    
    # make sure to write the new input`
    m.write_input()


def plotting_example(m, name):
    model_id = "NsmcBase" 
    model_name = model_id + "_" + name
    model_dir = os.path.join("flopy_data\{}".format(model_name))

    headfile = model_name + ".hds"
    hds = flopy.utils.HeadFile(model_dir + '/' + headfile)
    h = hds.get_data(kstpkper=(0, 0))
    f, ax = plt.subplots()
    modelmap = flopy.plot.ModelMap(model=m, ax=ax, layer=1)
    cv = modelmap.contour_array(h[1], levels=[10, 20, 30, 40, 50, 60, 70, 80, 90, 100], linewidths=0.5,colors="black")
    k = modelmap.plot_array(np.log(m.upw.hk[1].array), cmap = "jet", vmin=-2, vmax=8)
    cb = plt.colorbar(k, extend = 'both')
    cb.ax.set_title('log(K)', fontsize = 'small')
    plt.clabel(cv, fmt="%2.1f")
    plt.show()


def plot_cod(name0, name1):
    """ kind of plot the cone of depression: the difference in heads between two models
    
        inputs: 
            name0, name1: the names of the models

        Plots an array of contours, using the ModelTools which I've modified
    """
    model_id = "NsmcBase" 
    h = [[],[]]

    m = load_model(name0)

    # get array of head differences
    for i, name in enumerate([name0, name1]):
        model_name = model_id + "_" + name
        model_dir = os.path.join("flopy_data\{}".format(model_name))
        headfile = model_name + ".hds"
        hds = flopy.utils.HeadFile(model_dir + '/' + headfile)
        h[i] = hds.get_data(kstpkper=(0, 0))


    h_diff = h[0] - h[1]
    print(h_diff)




    ## With Conductivity ##
    f, ax = plt.subplots()
    modelmap = flopy.plot.ModelMap(model=m, ax=ax, layer=0)
    cv = modelmap.contour_array(h_diff[0], levels=np.linspace(0.,5., 10), linewidths=0.5,colors="black")
    k = modelmap.plot_array(np.log(m.upw.hk[0].array), cmap = "jet", vmin=-2, vmax=8, alpha=0.5)
    cb = plt.colorbar(k, extend = 'both')
    cb.ax.set_title('log(K)', fontsize = 'small')
    plt.clabel(cv, fmt="%2.1f", fontsize='x-small')

    ## With Basemap ##
    #f, ax = smt.plt_matrix(array=h_diff[0], title="Cone of Depression", base_map=True, color_bar=False)
    plt.show()


def main():

    name = "test0"

    m = import_model(name)
    m = load_model("test0")
    run_model(m)
    m_copy = copy_model(m, "copy0")
    # plotting_example(m, name)
    gshp_abs, gshp_inj = gshp_well_data()
    for i in range (0, len(gshp_abs)):
        """Loop through each col to get lon, lat, q and elv"""
        add_well(m_copy, gshp_abs.loc[i,'NZTMX'], gshp_abs.loc[i,'NZTMY'], gshp_abs.loc[i,'Depth'], -60*60*24*gshp_abs.loc[i,'Max Rate']/1000)
        i=i+1
    for i in range (0, len(gshp_inj)):
        """Loop through each col to get lon, lat, q and elv"""
        add_well(m_copy, gshp_inj.loc[i,'NZTMX'], gshp_inj.loc[i,'NZTMY'], gshp_inj.loc[i,'Depth'], 60*60*24*gshp_inj.loc[i,'Max Rate']/1000)
        i=i+1
    #yadd_well(m_copy, 1560354, 5204192, 48, -100000)
    run_model(m_copy)
    plot_cod("test0", "copy0")

    pass


if __name__ == "__main__":
    main()
    
    
