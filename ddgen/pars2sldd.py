import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))  # Adjust path as needed
from ddgen import slddgen
import pandas as pd
import numpy as np

def get_coder_info(name):
    match name:
        case "import_from_file":
        
            ElementClass="Simulink.Parameter"
            coder_info ={
                "StorageClass": "Custom",
                "TypeQualifier": "",
                "Alias": "parm_ApdrvChn1InpRng",
                "Alignment": -1.0,
                "CSCPackageName": "Simulink",
                "ParameterOrSignal": "Parameter",
                "CustomStorageClass": "ImportFromFile",
                "CustomAttributes": {
                    "HeaderFile": "generated_params.h",
                    "ConcurrentAccess": False
                }
            }
        case "eco":
            ElementClass="EcoObj.Parameter"
            coder_info={
                "CSCPackageName": "EcoObj",
                    "ParameterOrSignal": "Parameter",
                    "CustomStorageClass": "Calibration",           
            }
        
    return (ElementClass,coder_info)
    
def create_pars_entries_from_xls(xsl_file,par_type):
    """
    Read a DBC file and create a Simulink Data Dictionary with buses for each CAN message.
    
    Args:
        dbc_file (str): Path to the input DBC file.
        output_file (str): Path to the output .sldd file.
    """
    # Load DBC file
    # db = canmatrix.formats.loadp(dbc_file, "dbc")
    ElementClass,coder_info=get_coder_info(par_type)
    
    df=pd.read_excel(xsl_file)
    pars_entries=[]
    value_fld_names=['Value_'+str(i+1) for i in range(10)]
    col_names=df.columns.values
    col_names1=[ s.replace(' ','') for s in col_names]
    col_dict=dict(zip(col_names,col_names1))
    df.rename(columns=col_dict,inplace=1)
    for index, row in df.iterrows():
        dims=[row['Dimensions_1'], row['Dimensions_2']]
        dim_max = max(dims)
        
        values = row[value_fld_names].values
        val=values[0:dim_max].tolist()
        # val=[v.item() for v in val]
        if np.isnan(val).any():
            print('!')
        # if len(val)==1:
        #     val=val[0]
            
        param_dict = {
        "ElementClass": ElementClass,
        "Name": row['Name'],
        "Dimensions": dims,
        "Value": val,
        "Units": row['Unit'],
        "Description": row["Description"],
        "DataType": row["DataType"],
        "Min": row["Min"],
        "Max": row["Max"],
        "CoderInfo": coder_info
    }
        pars_entries.append(param_dict)
        
    return pars_entries


    

# def bus_entries_preproc():
#     """
#     Preprocess bus entries to ensure they are in the correct format.
    
#     Returns:
#         list: List of bus entries with each entry as a tuple (bus_name, elements).
#     """
#     # Example preprocessing logic
#     # This can be customized based on specific requirements
#     # bus_entries = create_bus_entries_from_dbc("example.dbc")
#     for bus_name, elements in bus_entries:
#         # Ensure each element has required keys
        
#         for element in elements:
#             if not isinstance(element, dict):
#                 raise ValueError(f"Element {element} in bus {bus_name} is not a dictionary.")
#             if "Name" not in element or "DataType" not in element or "Dimensions" not in element:
#                 raise ValueError(f"Element {element} in bus {bus_name} is missing required keys.")
        
#     return bus_entries
def pars2sldd_gen(inp_file,par_type="import_from_file"):
    """
    Generate a Simulink Data Dictionary from a DBC file.
    
    This function reads a DBC file, extracts CAN messages and their signals,
    and creates a Simulink Data Dictionary with buses for each message.
    
    Returns:
        None
    """
    # Example DBC file path (replace with actual path)
    # dbc_file = "example.dbc"
    sldd_name= os.path.splitext(os.path.basename(inp_file))[0] + ".sldd"
    sldd_path = os.path.join(os.path.dirname(inp_file), sldd_name)
    # Create Simulink Data Dictionary from DBC
    pars_entries=create_pars_entries_from_xls(inp_file,par_type)
    # print([msg for (msg,_) in bus_entries])
    slddgen.create_simulink_dd(sldd_path,params_entries=pars_entries)
    print(f"\nSimulink Data Dictionary '{sldd_name}' created successfully from {inp_file} file.\npath:{sldd_path}")

# Example usage
if __name__ == "__main__":
    # Example DBC file path (replace with actual path)
    inp_file = r"C:\D\proj\gh\sl2py\data\params.xlsx"
    pars2sldd_gen(inp_file,par_type="eco")
    # output_sldd = "MyDataDictionary.sldd"
    # sldd_name= os.path.splitext(os.path.basename(dbc_file))[0] + ".sldd"
    # # Create Simulink Data Dictionary from DBC
    # bus_entries=create_bus_entries_from_dbc(dbc_file)
    # print(bus_entries)
    # slddgen.create_simulink_dd(bus_entries, f"data/{sldd_name}")
    # print(f"Simulink Data Dictionary '{sldd_name}' created successfully from DBC file.")
    