import xml.etree.ElementTree as ET
import zipfile
import os
import uuid
from datetime import datetime
from xml.dom import minidom

NAMESPACE = "dacaf35e-55a5-454d-a7c1-93db038a210e"

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

def create_simulink_bus(root,bus_name, elements):
    """
    Create a Simulink Bus XML element.
    
    Args:
        bus_name (str): Name of the Simulink Bus.
        elements (list): List of dictionaries with keys: Name, DataType, Dimensions, Description (optional), DocUnits (optional).
    
    Returns:
        ET.Element: The Simulink.Bus XML element.
    """
    bus_element=create_bus(bus_name, elements)
    obj = ET.SubElement(root, "Object", Class="DD.ENTRY")
    ET.SubElement(obj, "P", Name="Name", Class="char").text = bus_name
    ET.SubElement(obj, "P", Name="UUID", Class="char").text = str(uuid.uuid4())
    ET.SubElement(obj, "P", Name="Namespace", Class="char").text = NAMESPACE
    ET.SubElement(obj, "P", Name="LastMod", Class="char").text = datetime.now().strftime("%Y%m%dT%H%M%S.%f")
    ET.SubElement(obj, "P", Name="LastModBy", Class="char").text = "robot"
    ET.SubElement(obj, "P", Name="IsDerived", Class="char").text = "0"
    value = ET.SubElement(obj, "P", Name="Value")
    value.append(bus_element)
    return

# def indent(elem, level=0):
#     """Add indentation to an XML element for pretty printing."""
#     indent_str = "  "  # Two spaces per level
#     if len(elem):
#         if not elem.text or not elem.text.strip():
#             elem.text = "\n" + indent_str * (level + 1)
#         if not elem.tail or not elem.tail.strip():
#             elem.tail = "\n" + indent_str * level
#         for child in elem:
#             indent(child, level + 1)
#         if not elem.tail or not elem.tail.strip():
#             elem.tail = "\n" + indent_str * level
#     else:
#         if level and (not elem.tail or not elem.tail.strip()):
#             elem.tail = "\n" + indent_str * level

def create_simulink_dd(bus_entries, output_file):
    """
    Create a Simulink Data Dictionary with a Bus object and additional files, saved as a zipped .sldd.
    
    Args:
        bus_name (str): Name of the Simulink Bus.
        bus_element (ET.Element): The Simulink.Bus XML element.
        output_file (str): Path to the output .sldd file.
    """
    # Create temporary directory for files
    temp_dir = "temp_sldd"
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "_rels"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "data"), exist_ok=True)

    # Create [Content_Types].xml
    content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default ContentType="application/vnd.openxmlformats-package.relationships+xml" Extension="rels"/>
    <Default ContentType="application/vnd.mathworks.simulink.data.dictionaryChunk+xml" Extension="xml"/>
</Types>'''
    # Parse and pretty-print [Content_Types].xml
    content_types_xml = minidom.parseString(content_types)
    with open(os.path.join(temp_dir, "[Content_Types].xml"), "w", encoding="utf-8") as f:
        f.write(content_types_xml.toprettyxml(indent="  ", newl="\n", encoding="utf-8").decode("utf-8"))

    # Create _rels/.rels
    rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Target="data/chunk0.xml" Type="http://schemas.mathworks.com/simulink/2010/relationships/dictionaryChunk"/>
</Relationships>'''
    # Parse and pretty-print _rels/.rels
    rels_xml = minidom.parseString(rels)
    with open(os.path.join(temp_dir, "_rels", ".rels"), "w", encoding="utf-8") as f:
        f.write(rels_xml.toprettyxml(indent="  ", newl="\n", encoding="utf-8").decode("utf-8"))

    # Create data/chunk0.xml
    root = ET.Element("DataSource", FormatVersion="1", MinRelease="R2014a", Arch="win64")
    # obj = ET.SubElement(root, "Object", Class="DD.ENTRY")
    # ET.SubElement(obj, "P", Name="Name", Class="char").text = bus_name
    # ET.SubElement(obj, "P", Name="UUID", Class="char").text = str(uuid.uuid4())
    # ET.SubElement(obj, "P", Name="Namespace", Class="char").text = namespace
    # ET.SubElement(obj, "P", Name="LastMod", Class="char").text = datetime.now().strftime("%Y%m%dT%H%M%S.%f")
    # ET.SubElement(obj, "P", Name="LastModBy", Class="char").text = "user"
    # ET.SubElement(obj, "P", Name="IsDerived", Class="char").text = "0"
    # value = ET.SubElement(obj, "P", Name="Value")
    # value.append(bus_element)
    for bus_name, bus_elements in bus_entries:
        create_simulink_bus(root,bus_name, bus_elements)
    dict_obj = ET.SubElement(root, "Object", Class="DD.Dictionary")
    ET.SubElement(dict_obj, "P", Name="AccessBaseWorkspace", Class="logical").text = "0"

    # Apply indentation to chunk0.xml
    # ET.indent(root, '  ')
    # indent(root)
    chunk0_file = os.path.join(temp_dir, "data", "chunk0.xml")
    tree = ET.ElementTree(root)
    # with open(chunk0_file, "wb") as f:
    tree.write(chunk0_file, encoding="utf-8", xml_declaration=True)
    xmlDom = minidom.parse(chunk0_file)

    prettyXML = xmlDom.toprettyxml(encoding="UTF-8",indent="  ")

    myfile = open(chunk0_file, mode="wb")
    myfile.write(prettyXML)
    myfile.close()
    # Create .sldd file (zipped archive)
    with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(os.path.join(temp_dir, "[Content_Types].xml"), "[Content_Types].xml")
        zf.write(os.path.join(temp_dir, "_rels", ".rels"), "_rels/.rels")
        zf.write(chunk0_file, "data/chunk0.xml")

    # Clean up temporary directory
    import shutil
    shutil.rmtree(temp_dir)

# Example usage
if __name__ == "__main__":
    # Define Bus elements as a list of dictionaries
    bus_entries=[]
    bus_elements1 = [
        {"Name": "MyBoolVar", "DataType": "boolean", "Dimensions": 1, "Description": "Is Message Available"},
        {"Name": "MyUint16Var", "DataType": "uint16", "Dimensions": 1},
        {"Name": "MySingleVar", "DataType": "single", "Dimensions": 1}
    ]
    bus_elements2 = [
    {"Name": "MyBoolVar2", "DataType": "boolean", "Dimensions": 1, "Description": "Is Message Available"},
    {"Name": "MyUint8Var", "DataType": "uint8", "Dimensions": 1},
    {"Name": "MyDoubleVar", "DataType": "double", "Dimensions": 1}
    ]
    bus_entries.append(('MyBus1',bus_elements1))
    bus_entries.append(('MyBus2',bus_elements2))
    
    # Create Simulink Bus XML element
    # bus = create_simulink_bus("MyBus", bus_elements)
    
    # Create Data Dictionary with the Bus
    create_simulink_dd(bus_entries, "data/MyDataDictionary.sldd")
    print(f"Simulink Data Dictionary 'MyDataDictionary.sldd' created successfully.")