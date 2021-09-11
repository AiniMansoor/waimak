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

ToDo: 
    - functionalize this code:
        -> save a copy?

    - set up some code outlines for Ella and Aine, adding wells etc.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import flopy_mh as flopy
from waimak_extended_boundry.model_run_tools.model_setup.base_modflow_wrapper import import_gns_model
import shapely
from shapely.geometry.point import Point


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

def main():

    name = "test0"

    import_model(name)
    m = load_model(name)
    run_model(m)
    # add_well_example(m)
    plotting_example(m, name)

if __name__ == "__main__":
    main()

