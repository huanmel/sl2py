import os
from canmatrix import canmatrix
import sys
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
            
def create_bus_entries_from_dbc(dbc_file):
    """
    Read a DBC file and create a Simulink Data Dictionary with buses for each CAN message.
    
    Args:
        dbc_file (str): Path to the input DBC file.
        output_file (str): Path to the output .sldd file.
    """
    # Load DBC file
    # db = canmatrix.formats.loadp(dbc_file, "dbc")
    db = canmatrix.formats.loadp_flat(str(dbc_file))
    dbc_name=os.path.basename(dbc_file)
    # for frame in dbc.frames:
    # Create bus entries for each message
    bus_entries = []
    element_avl_dict = {
                "Name": "IsMsgAvl",
                "DataType": 'boolean',
                "Dimensions": 1,  # Signals are typically scalar in CAN messages
                "Description": "Is Message Available",
                "Units": ""
            }
    for message in db.frames:
        # Prepare signal elements for the message
        elements = []
        for signal in message.signals:
            element_dict = {
                "Name": signal.name,
                "DataType": propose_data_type(signal),
                "Dimensions": 1,  # Signals are typically scalar in CAN messages
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
        bus_name ="CAN_"+message.name+"_t"
        # bus_element = create_simulink_bus(bus_name, elements)
        bus_entries.append((bus_name, elements))
        
    return bus_entries

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
def dbc2sldd_gen(dbc_file):
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
    # Create Simulink Data Dictionary from DBC
    bus_entries=create_bus_entries_from_dbc(dbc_file)
    print([msg for (msg,_) in bus_entries])
    slddgen.create_simulink_dd(bus_entries,sldd_path)
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
    