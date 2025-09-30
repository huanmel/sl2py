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

def create_bus(elements):
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
    bus_value=create_bus(elements)
    create_dd_entry(root,bus_name,bus_value)
    # ET.SubElement(root,obj)
    # obj = ET.SubElement(root, "Object", Class="DD.ENTRY")
    # ET.SubElement(obj, "P", Name="Name", Class="char").text = bus_name
    # ET.SubElement(obj, "P", Name="UUID", Class="char").text = str(uuid.uuid4())
    # ET.SubElement(obj, "P", Name="Namespace", Class="char").text = NAMESPACE
    # ET.SubElement(obj, "P", Name="LastMod", Class="char").text = datetime.now().strftime("%Y%m%dT%H%M%S.%f")
    # ET.SubElement(obj, "P", Name="LastModBy", Class="char").text = "robot"
    # ET.SubElement(obj, "P", Name="IsDerived", Class="char").text = "0"
    # value = ET.SubElement(obj, "P", Name="Value")
    # value.append(bus_with_elements)
    return

def create_dd_entry(root,name,value_cont):
    obj = ET.SubElement(root, "Object", Class="DD.ENTRY")
    ET.SubElement(obj, "P", Name="Name", Class="char").text = name
    ET.SubElement(obj, "P", Name="UUID", Class="char").text = str(uuid.uuid4())
    ET.SubElement(obj, "P", Name="Namespace", Class="char").text = NAMESPACE
    ET.SubElement(obj, "P", Name="LastMod", Class="char").text = datetime.now().strftime("%Y%m%dT%H%M%S.%f")
    ET.SubElement(obj, "P", Name="LastModBy", Class="char").text = "robot"
    ET.SubElement(obj, "P", Name="IsDerived", Class="char").text = "0"
    value = ET.SubElement(obj, "P", Name="Value")
    value.append(value_cont)
    return

def create_param_entry_value(param_dict):
    """
    Create a Simulink Data Dictionary parameter entry from an input dictionary.
    
    Args:
        param_dict (dict): Dictionary with fields:
            - ElementClass (str, optional): Parameter class, defaults to 'Simulink.Parameter'.
            - Name (str): Parameter name.
            - Dimensions (list): List of two integers [rows, cols].
            - Value (list): List of values matching dimensions.
            - Units (str): Units for DocUnits.
            - Description (str, optional): Parameter description.
            - DataType (str, optional): Data type, defaults based on Value.
            - Min (float, optional): Minimum value, defaults to 0.0.
            - Max (float, optional): Maximum value, defaults to 100.0.
            - CoderInfo (dict): Nested dictionary with:
                - StorageClass (str): Typically 'Custom'.
                - TypeQualifier (str): Often empty.
                - Alias (str, optional): Alias name.
                - Alignment (float): Typically -1.0.
                - CSCPackageName (str): Package name (e.g., 'EcoObj', 'Simulink').
                - ParameterOrSignal (str): Typically 'Parameter'.
                - CustomStorageClass (str): e.g., 'Calibration', 'ImportFromFile'.
                - CustomAttributes (dict): Attributes like HeaderFile, ConcurrentAccess.
                - HasCoderInfo (bool, optional): Defaults to True.
                - IsCSCPackageOverridden (bool, optional): Defaults to False.
    
    Returns:
        ET.Element: XML element for <Object Class="DD.ENTRY">.
    """
    # Validate and set defaults
    element_class = param_dict.get("ElementClass", "Simulink.Parameter")
    name = param_dict["Name"]
    dimensions = param_dict["Dimensions"]
    value = param_dict["Value"]
    units = param_dict["Units"]
    description = param_dict.get("Description", "")
    min_val = param_dict.get("Min", 0.0)
    max_val = param_dict.get("Max", 100.0)
    coder_info = param_dict.get("CoderInfo", {})
    
    # Determine DataType if not provided
    data_type = param_dict.get("DataType")
    if not data_type:
        if all(isinstance(v, bool) for v in value):
            data_type = "boolean"
        elif all(isinstance(v, float) for v in value):
            data_type = "single" if len(value) <= 2 else "double"
        else:
            data_type = "uint8"  # Default for integers
    
    # Validate dimensions and value
    if len(dimensions) != 2:
        raise ValueError("Dimensions must be a list of two integers")
    if len(value) != dimensions[0] * dimensions[1]:
        raise ValueError(f"Value length ({len(value)}) must match dimensions ({dimensions[0]}*{dimensions[1]})")

    # Create DD.ENTRY object
    # obj = ET.Element("Object", Class="DD.ENTRY")
    # ET.SubElement(obj, "P", Name="Name", Class="char").text = name
    # ET.SubElement(obj, "P", Name="UUID", Class="char").text = str(uuid.uuid4())
    # ET.SubElement(obj, "P", Name="Namespace", Class="char").text = "dacaf35e-55a5-454d-a7c1-93db038a210e"
    # ET.SubElement(obj, "P", Name="LastMod", Class="char").text = datetime.now().strftime("%Y%m%dT%H%M%S.%f")
    # ET.SubElement(obj, "P", Name="LastModBy", Class="char").text = "user"
    # ET.SubElement(obj, "P", Name="IsDerived", Class="char").text = "0"

    # Create Value element
    #    bus = ET.Element("Element", Class="Simulink.Bus")
    # value_elem = ET.SubElement(obj, "P", Name="Value")
 
    param = ET.Element("Element", Class=element_class)
    
    # Add Value
    value_str = " ".join(str(v) for v in value)
    ET.SubElement(param, "P", Name="Value", Class=data_type, Dimension=f"1*{len(value)}").text = value_str
    
    # Add other parameter properties
    ET.SubElement(param, "P", Name="Complexity", Class="char").text = "real"
    ET.SubElement(param, "P", Name="Dimensions", Class="double", Dimension="1*2").text = f"{dimensions[0]}.0 {dimensions[1]}.0"
    ET.SubElement(param, "P", Name="Description", Class="char").text = description
    ET.SubElement(param, "P", Name="DataType", Class="char").text = data_type
    ET.SubElement(param, "P", Name="Min", Class="double").text = str(min_val)
    ET.SubElement(param, "P", Name="Max", Class="double").text = str(max_val)
    ET.SubElement(param, "P", Name="DocUnits", Class="char").text = units
    if data_type in ["single", "double"]:
        ET.SubElement(param, "P", Name="DimensionsMode", Class="char").text = "Fixed"

    # Create CoderInfo
    if coder_info:
        coder_info_elem = ET.SubElement(param, "P", Name="CoderInfo")
        coder_info_sub = ET.SubElement(coder_info_elem, "Element", Class="Simulink.CoderInfo")
        ET.SubElement(coder_info_sub, "P", Name="HasCoderInfo", Class="logical").text = str(int(coder_info.get("HasCoderInfo", True)))
        ET.SubElement(coder_info_sub, "P", Name="StorageClass", Class="char").text = coder_info.get("StorageClass", "Custom")
        ET.SubElement(coder_info_sub, "P", Name="TypeQualifier", Class="char").text = coder_info.get("TypeQualifier", "")
        ET.SubElement(coder_info_sub, "P", Name="Alias", Class="char").text = coder_info.get("Alias", "")
        ET.SubElement(coder_info_sub, "P", Name="Alignment", Class="double").text = str(coder_info.get("Alignment", -1.0))
        ET.SubElement(coder_info_sub, "P", Name="IsCSCPackageOverridden", Class="logical").text = str(int(coder_info.get("IsCSCPackageOverridden", False)))
        ET.SubElement(coder_info_sub, "P", Name="CSCPackageName", Class="char").text = coder_info.get("CSCPackageName", "Simulink")
        ET.SubElement(coder_info_sub, "P", Name="ParameterOrSignal", Class="char").text = coder_info.get("ParameterOrSignal", "Parameter")
        ET.SubElement(coder_info_sub, "P", Name="CustomStorageClass", Class="char").text = coder_info.get("CustomStorageClass", "Calibration")

        # Add CustomAttributes
        custom_attrs = coder_info.get("CustomAttributes", {})
        custom_attrs_elem = ET.SubElement(coder_info_sub, "P", Name="CustomAttributes")
        attr_class = f"SimulinkCSC.AttribClass_{coder_info.get('CSCPackageName', 'Simulink')}_{coder_info.get('CustomStorageClass', 'Calibration')}"
        attr_elem = ET.SubElement(custom_attrs_elem, "Element", Class=attr_class)
        ET.SubElement(attr_elem, "P", Name="HeaderFile", Class="char").text = custom_attrs.get("HeaderFile", "")
        if coder_info.get("CustomStorageClass") == "ImportFromFile":
            ET.SubElement(attr_elem, "P", Name="ConcurrentAccess", Class="logical").text = str(int(custom_attrs.get("ConcurrentAccess", False)))

    return param

def create_simulink_param(root, param_dict):
    par_element=create_param_entry_value(param_dict)
    create_dd_entry(root,param_dict["Name"],par_element)
    return

def create_enum_entry_value(enum_dict):
    """
    Create an ET.Element representing a Simulink EnumTypeDefinition from a dictionary.
    Args:
        enum_dict (dict): {int_value: description_str}
    Returns:
        ET.Element: EnumTypeDefinition XML element
    """
    enum = ET.Element("Element", Class="Simulink.data.dictionary.EnumTypeDefinition")
    # Enumerals
    enumerals = ET.SubElement(enum, "P", Name="Enumerals", Class="struct", Dimension=f"1*{len(enum_dict)}")
    # Sort by value ascending
    for value, desc in sorted(enum_dict.items()):
        elem = ET.Element("Element")
        # Name: use description if not empty, else fallback to 'Value{value}'
        name = desc if desc else f"VALUE_{value}"
        ET.SubElement(elem, "P", Name="Name", Class="char").text = name
        ET.SubElement(elem, "P", Name="Value", Class="char").text = str(value)
        # description = "" if desc.startswith("Description for the value") or desc == name else desc
        ET.SubElement(elem, "P", Name="Description", Class="char").text = desc
        enumerals.append(elem)
    # Other required properties
    ET.SubElement(enum, "P", Name="Description", Class="char").text = ""
    ET.SubElement(enum, "P", Name="DataScope", Class="char").text = "Auto"
    ET.SubElement(enum, "P", Name="HeaderFile", Class="char").text = ""
    # DefaultValue: use first enumeral name
    first_name = next(iter(sorted(enum_dict.items())))[1]
    default_name = first_name if first_name and not first_name.startswith("Description for the value") else f"Value{next(iter(sorted(enum_dict.keys())))}"
    ET.SubElement(enum, "P", Name="DefaultValue", Class="char").text = default_name
    ET.SubElement(enum, "P", Name="StorageType", Class="char").text = ""
    ET.SubElement(enum, "P", Name="AddClassNameToEnumNames", Class="logical").text = "1"
    return enum

def create_simulink_enum(root, enum_dict):
    enum_dict_name=list(enum_dict.keys())[0]
    enum_dict_value=enum_dict[enum_dict_name]
    enum_element=create_enum_entry_value(enum_dict_value)
    create_dd_entry(root,enum_dict_name,enum_element)
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

def create_simulink_dd(output_file,params_entries=[],bus_entries=[], enum_entries=[]):
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
    for param_dict in params_entries:
        create_simulink_param(root, param_dict)
    for enum_dict in enum_entries:
        create_simulink_enum(root, enum_dict)
  
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
    coder_info_eco={
           "CSCPackageName": "EcoObj",
            "ParameterOrSignal": "Parameter",
            "CustomStorageClass": "Calibration",
            
    }
    param_dict = {
    "ElementClass": "EcoObj.Parameter",
    # "ElementClass": "Simulink.Parameter",
    "Name": "MyParameter",
    "Dimensions": [1, 2],
    "Value": [13.0, 96.8],
    "Units": "%",
    "Description": "Accelerator pedal driver: Channel1InputRange - 1st channel extreme voltage ratio",
    "DataType": "single",
    "Min": 0.0,
    "Max": 100.0,
    "CoderInfo": coder_info_eco
}
    param_entries = [param_dict]
    
    
    enum_entries=[{'MyEnum':{7: 'NA',
 6: 'ERR',
 5: "Description for the value '0x5'",
 4: "Description for the value '0x4'",
 3: "Description for the value '0x3'",
 2: "Description for the value '0x2'",
 1: 'Value1',
 0: 'Value0'}}]
    # Create Data Dictionary with the Bus
    create_simulink_dd("data/MyDataDictionary.sldd",bus_entries=bus_entries,params_entries=param_entries, enum_entries=enum_entries)
    # create_simulink_dd("data/MyDataDictionary.sldd",params_entries=param_entries)
    print(f"Simulink Data Dictionary 'MyDataDictionary.sldd' created successfully.")