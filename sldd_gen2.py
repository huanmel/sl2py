import xml.etree.ElementTree as ET
import zipfile
import os
import uuid
from datetime import datetime
from xml.dom import minidom
from canmatrix import canmatrix

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

def create_bus_element(element_dict):
    """Create a Simulink.BusElement XML element from a dictionary."""
    elem = ET.Element("Element", Class="Simulink.BusElement")
    ET.SubElement(elem, "P", Name="Min_internal", Class="double", Dimension="0*0")
    ET.SubElement(elem, "P", Name="Max_internal", Class="double", Dimension="0*0")
    ET.SubElement(elem, "P", Name="DimensionsMode", Class="char").text = "Fixed"
    ET.SubElement(elem, "P", Name="SamplingMode", Class="char").text = "Sample based"
    ET.SubElement(elem, "P", Name="SampleTime", Class="double").text = "-1.0"
    ET.SubElement(elem, "P", Name="Description", Class="char").text = element_dict.get("Description", "")
    ET.SubElement(elem, "P", Name="DocUnits", Class="char").text = element_dict.get("DocUnits", "")
    ET.SubElement(elem, "P", Name="Name", Class="char").text = element_dict["Name"]
    ET.SubElement(elem, "P", Name="DataType_internal", Class="char").text = element_dict["DataType"]
    ET.SubElement(elem, "P", Name="Complexity", Class="char").text = "real"
    ET.SubElement(elem, "P", Name="Dimensions", Class="double").text = str(element_dict["Dimensions"])
    return elem

def create_bus(bus_name, elements):
    """Create a Simulink.Bus XML element from a bus name and list of element dictionaries."""
    bus = ET.Element("Element", Class="Simulink.Bus")
    ET.SubElement(bus, "P", Name="Alignment", Class="double").text = "-1.0"
    ET.SubElement(bus, "P", Name="PreserveElementDimensions", Class="logical").text = "0"
    elements_prop = ET.SubElement(bus, "P", Name="Elements_internal", Dimension=f"{len(elements)}*1")
    for element_dict in elements:
        elements_prop.append(create_bus_element(element_dict))
    ET.SubElement(bus, "P", Name="Description", Class="char")
    ET.SubElement(bus, "P", Name="DataScope", Class="char").text = "Auto"
    ET.SubElement(bus, "P", Name="HeaderFile", Class="char")
    return bus

def create_simulink_bus(bus_name, elements):
    """
    Create a Simulink Bus XML element.
    
    Args:
        bus_name (str): Name of the Simulink Bus.
        elements (list): List of dictionaries with keys: Name, DataType, Dimensions, Description (optional), DocUnits (optional).
    
    Returns:
        ET.Element: The Simulink.Bus XML element.
    """
    return create_bus(bus_name, elements)

def create_simulink_dd(bus_entries, output_file):
    """
    Create a Simulink Data Dictionary with multiple Bus objects, saved as a zipped .sldd.
    All XML files use Unix-style line endings (\n).
    
    Args:
        bus_entries (list): List of tuples (bus_name, bus_element) for each bus.
        output_file (str): Path to the output .sldd file.
    """
    # Create temporary directory for files
    temp_dir = "temp_sldd"
    namespace = "dacaf35e-55a5-454d-a7c1-93db038a210e"
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "_rels"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "data"), exist_ok=True)

    # Create [Content_Types].xml
    content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default ContentType="application/vnd.openxmlformats-package.relationships+xml" Extension="rels"/>
    <Default ContentType="application/vnd.mathworks.simulink.data.dictionaryChunk+xml" Extension="xml"/>
</Types>'''
    content_types_xml = minidom.parseString(content_types)
    with open(os.path.join(temp_dir, "[Content_Types].xml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(content_types_xml.toprettyxml(indent="  ", newl="\n", encoding="utf-8").decode("utf-8"))

    # Create _rels/.rels
    rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Target="data/chunk0.xml" Type="http://schemas.mathworks.com/simulink/2010/relationships/dictionaryChunk"/>
</Relationships>'''
    rels_xml = minidom.parseString(rels)
    with open(os.path.join(temp_dir, "_rels", ".rels"), "w", encoding="utf-8", newline="\n") as f:
        f.write(rels_xml.toprettyxml(indent="  ", newl="\n", encoding="utf-8").decode("utf-8"))

    # Create data/chunk0.xml
    root = ET.Element("DataSource", FormatVersion="1", MinRelease="R2014a", Arch="win64")
    for bus_name, bus_element in bus_entries:
        obj = ET.SubElement(root, "Object", Class="DD.ENTRY")
        ET.SubElement(obj, "P", Name="Name", Class="char").text = bus_name
        ET.SubElement(obj, "P", Name="UUID", Class="char").text = str(uuid.uuid4())
        ET.SubElement(obj, "P", Name="Namespace", Class="char").text = namespace
        ET.SubElement(obj, "P", Name="LastMod", Class="char").text = datetime.now().strftime("%Y%m%dT%H%M%S.%f")
        ET.SubElement(obj, "P", Name="LastModBy", Class="char").text = "user"
        ET.SubElement(obj, "P", Name="IsDerived", Class="char").text = "0"
        value = ET.SubElement(obj, "P", Name="Value")
        value.append(bus_element)
    dict_obj = ET.SubElement(root, "Object", Class="DD.Dictionary")
    ET.SubElement(dict_obj, "P", Name="AccessBaseWorkspace", Class="logical").text = "0"

    # Write chunk0.xml with pretty printing
    chunk0_file = os.path.join(temp_dir, "data", "chunk0.xml")
    tree = ET.ElementTree(root)
    tree.write(chunk0_file, encoding="utf-8", xml_declaration=True)
    xml_dom = minidom.parse(chunk0_file)
    with open(chunk0_file, "wb", newline="\n") as f:
        f.write(xml_dom.toprettyxml(indent="  ", newl="\n", encoding="utf-8"))

    # Create .sldd file (zipped archive)
    with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(os.path.join(temp_dir, "[Content_Types].xml"), "[Content_Types].xml")
        zf.write(os.path.join(temp_dir, "_rels", ".rels"), "_rels/.rels")
        zf.write(chunk0_file, "data/chunk0.xml")

    # Clean up temporary directory
    import shutil
    shutil.rmtree(temp_dir)

def create_sldd_from_dbc(dbc_file, output_file):
    """
    Read a DBC file and create a Simulink Data Dictionary with buses for each CAN message.
    
    Args:
        dbc_file (str): Path to the input DBC file.
        output_file (str): Path to the output .sldd file.
    """
    # Load DBC file
    db = canmatrix.formats.loadp(dbc_file, "dbc")
    
    # Create bus entries for each message
    bus_entries = []
    for message in db.frames:
        # Prepare signal elements for the message
        elements = []
        for signal in message.signals:
            element_dict = {
                "Name": signal.name,
                "DataType": propose_data_type(signal),
                "Dimensions": 1,  # Signals are typically scalar in CAN messages
                "Description": signal.comment or "",
                "DocUnits": signal.unit or ""
            }
            elements.append(element_dict)
        
        # Create bus for the message
        bus_name = message.name
        bus_element = create_simulink_bus(bus_name, elements)
        bus_entries.append((bus_name, bus_element))
    
    # Create Simulink Data Dictionary
    create_simulink_dd(bus_entries, output_file)

# Example usage
if __name__ == "__main__":
    # Example DBC file path (replace with actual path)
    dbc_file = "example.dbc"
    output_sldd = "MyDataDictionary.sldd"
    
    # Create Simulink Data Dictionary from DBC
    create_sldd_from_dbc(dbc_file, output_sldd)
    print(f"Simulink Data Dictionary '{output_sldd}' created successfully from DBC file.")