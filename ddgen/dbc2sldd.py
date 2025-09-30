import os
from canmatrix import canmatrix
import sys
import yaml

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))  # Adjust path as needed
from ddgen import slddgen

def propose_data_type(signal):
    """
    Propose a Simulink data type for a CAN signal based on its properties.
    
    Args:
        signal: canmatrix Signal object with attributes like size, is_signed, factor, offset.
    
    Returns:
        str: Proposed Simulink data type.
    """
    # Default values for optional signal attributes
    bit_length = signal.size
    is_signed = signal.is_signed
    factor = float(signal.factor) if signal.factor is not None else 1.0
    offset = float(signal.offset) if signal.offset is not None else 0.0

    # Handle boolean case
    if bit_length == 1:
        return "boolean"

    # Check if floating-point is required
    requires_float = factor != 1.0 or offset != 0.0

    if requires_float:
        # Use single precision unless bit length exceeds 32
        if bit_length <= 32:
            return "single"
        else:
            return "double"
    else:
        # Select integer type based on signedness and bit length
        if is_signed:
            if bit_length <= 8:
                return "int8"
            elif bit_length <= 16:
                return "int16"
            elif bit_length <= 32:
                return "int32"
            else:
                return "int64"
        else:
            if bit_length <= 8:
                return "uint8"
            elif bit_length <= 16:
                return "uint16"
            elif bit_length <= 32:
                return "uint32"
            else:
                return "uint64"
            
def create_bus_entries_from_dbc(dbc_file,conf=None):
    """
    Read a DBC file and create Simulink Data Dictionary buses and enums for each CAN message.
    Args:
        dbc_file (str): Path to the input DBC file.
    Returns:
        tuple: (bus_entries, EnumsExport)
    """
    db = canmatrix.formats.loadp_flat(str(dbc_file))
    dbc_name = os.path.basename(dbc_file)
    if conf:
        if dbc_name in conf:
            conf=conf[dbc_name]
        else:
            conf=None
            
    bus_entries = []
    EnumsExport = []
    # Copy value tables (enumerations) from db
    db_enums = dict(db.value_tables)
    
    # for enum in db_enums:
    def enum_name_proc(enum_name):
        new_enum_name=enum_name
        if not enum_name.endswith('_enum'):
            new_enum_name = enum_name + '_enum'
        if conf['enum_prefix'] and not new_enum_name.startswith(conf['enum_prefix'] ): 
            new_enum_name = conf['enum_prefix'] +new_enum_name
        return new_enum_name
        
        
    enum_names=list(db_enums.keys())
    for enum_name in enum_names:
        # Ensure enum name ends with _enum
        new_enum_name=enum_name_proc(enum_name)
        # if not enum_name.endswith('_enum'):
        #     new_enum_name = enum_name + '_enum'
        # if conf['enum_prefix'] and not new_enum_name.startswith(conf['enum_prefix'] ): 
        #     new_enum_name = conf['enum_prefix'] +new_enum_name
        if not (new_enum_name == enum_name):
            db_enums[new_enum_name] = db_enums.pop(enum_name)
                
    element_avl_dict = {
                "Name": "IsMsgAvl",
                "DataType": 'boolean',
                "Dimensions": 1,  # Signals are typically scalar in CAN messages
                "Description": "Is Message Available",
                "Units": ""
            }
        # Helper to check if enum already exported
    def enum_in_export(enum_name):
        return any(enum_name in d for d in EnumsExport)
    import re
    def make_c_compatible(name):
        # Replace any non-alphanumeric or underscore with underscore
        new_enum_name=re.sub(r'[^a-zA-Z0-9_]', '_', name)
        if new_enum_name.startswith(('0','1','2','3','4','5','6','7','8','9')):
            new_enum_name='E_'+new_enum_name    
        return new_enum_name

    for message in db.frames:
        # Prepare signal elements for the message
        if message.name.startswith("VECTOR__INDEPENDENT_SIG"):
            # Skip messages that are not relevant for Simulink
            continue
        if conf and conf['msgs']:
            if message.name not in conf['msgs']:
                continue
            
        elements = []
        for signal in message.signals:
            # Check for enumeration
            enum_type = None
            enum_dict = None
            is_enum = isinstance(signal.values, dict) and bool(signal.values)
            # If signal.values matches a db_enums entry
            if is_enum:
                for enum_name, enum_table in db_enums.items():
                    if signal.values == enum_table:
                        # Ensure enum name ends with _enum
                        # if not enum_name.endswith('_enum'):
                        #     new_enum_name = enum_name + '_enum'
                        #     db_enums[new_enum_name] = db_enums.pop(enum_name)
                        #     enum_name = new_enum_name
                        #     enum_table = db_enums[enum_name]
                        enum_type = enum_name
                        enum_dict = enum_table
                        
                        break
                if enum_type:
                    # Use Enum: EnumName
                    data_type = f"Enum: {enum_type}"
                    # Export enum if not already
                    if not enum_in_export(enum_type):
                        EnumsExport.append({enum_type: enum_dict})
                elif signal.values:
                    # Create new enum for this signal
                    # enum_type = signal.name + "_enum"
                    enum_type=enum_name_proc(signal.name)
                    enum_dict = signal.values
                    data_type = f"Enum: {enum_type}"
                    db_enums[enum_type] = enum_dict
                    if not enum_in_export(enum_type):
                        EnumsExport.append({enum_type: enum_dict})
            else:
                data_type = propose_data_type(signal)
            element_dict = {
                "Name": signal.name,
                "DataType": data_type,
                "IsEnum": is_enum,
                "Dimensions": 1,
                "Description": signal.comment or "",
                "Units": signal.unit or ""
            }
            elements.append(element_dict)
        # sort elements by name
        elements.sort(key=lambda x: x["Name"])
        # Add availability signal at the start
        if not any(el["Name"] == "IsMsgAvl" for el in elements):
            # Ensure availability signal is present
            elements.insert(0, element_avl_dict)  # Insert availability signal at the start
        # Create bus for the message
        bus_name ="CAN_MSG_"+message.name+"_t"
        # bus_element = create_simulink_bus(bus_name, elements)
        bus_entries.append((bus_name, elements))

    # Post-process EnumsExport for C compatibility
    for enum in EnumsExport:
        for enum_name, enum_table in enum.items():
            # Ensure enum name ends with _enum
            if not enum_name.endswith('_enum'):
                new_enum_name = enum_name + '_enum'
                enum[new_enum_name] = enum.pop(enum_name)
                enum_name = new_enum_name
                enum_table = enum[enum_name]
            # Replace C-incompatible symbols in enum value names
            for k in list(enum_table.keys()):
                v = enum_table[k]
                if v is None  or (v and (v == '' or v.isspace() or  v.startswith("Description for the value"))):
                    v1 = f"VALUE_{k}"
                else:
                    v1=v
                # v1 = v if v and not v.startswith("Description for the value") else f"VALUE_{k}"
                
                new_v = make_c_compatible(v1) if isinstance(v1, str) else v1
                if new_v != v:
                    enum_table[k] = new_v
    return bus_entries, EnumsExport

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
def dbc2sldd_gen(dbc_file,conf=None):
    """
    Generate a Simulink Data Dictionary from a DBC file.
    
    This function reads a DBC file, extracts CAN messages and their signals,
    and creates a Simulink Data Dictionary with buses for each message.
    
    Returns:
        None
    """
    # Example DBC file path (replace with actual path)
    # dbc_file = "example.dbc"
    sldd_name= os.path.splitext(os.path.basename(dbc_file))[0] + ".sldd"
    sldd_path = os.path.join(os.path.dirname(dbc_file), sldd_name)
    conf_file= os.path.join(os.path.dirname(dbc_file), "generate.yml")
    conf=None
    if os.path.exists(conf_file):
        with open(conf_file, 'r') as file:
            conf = yaml.safe_load(file)

    # Create Simulink Data Dictionary from DBC
    bus_entries, enums_entries =create_bus_entries_from_dbc(dbc_file,conf)
    print([msg for (msg,_) in bus_entries])
    slddgen.create_simulink_dd(sldd_path,bus_entries=bus_entries,enum_entries=enums_entries)
    print(f"\nSimulink Data Dictionary '{sldd_name}' created successfully from DBC file.\npath:{sldd_path}")

# Example usage
if __name__ == "__main__":
    # Example DBC file path (replace with actual path)
    dbc_file = r"C:\D\proj\gh\sl2py\data\example.dbc"
    dbc2sldd_gen(dbc_file)
    # output_sldd = "MyDataDictionary.sldd"
    # sldd_name= os.path.splitext(os.path.basename(dbc_file))[0] + ".sldd"
    # # Create Simulink Data Dictionary from DBC
    # bus_entries=create_bus_entries_from_dbc(dbc_file)
    # print(bus_entries)
    # slddgen.create_simulink_dd(bus_entries, f"data/{sldd_name}")
    # print(f"Simulink Data Dictionary '{sldd_name}' created successfully from DBC file.")
    