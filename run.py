import regex as re
import sys

def extract_methods(pyx_file, out_name = None):
    import json
    with open(pyx_file, "r") as fp:
        lines = fp.readlines()
    
    found = False

    methods = []
    method = ""
    method_indent = 0
    class_name = ""
    
    fun_class = "static"
    for l in lines:
        _l = l.strip()
        if (_l.startswith("cdef class ") or _l.startswith("class ") ):
            class_name = _l.split("class ")[1].split("(")[0]
        elif not found and (_l.startswith("def")): # or l.startswith("cdef") or l.startswith("cpdef")
            found = True
            method += _l
            method_indent = len(l) - len(l.lstrip())
            fun_class = "static" if method_indent == 0 else class_name
        elif found and _l.endswith("):"):
            method += _l[:-1]
            found = False
            methods.append({"fun": method.split(":")[0], "class": fun_class})
            method = ""
            method_indent = 0
            fun_class = "static"
        elif found and "#" not in _l:
            method += _l
    
    if out_name is not None:
        with open(out_name, "w") as fp:
            json.dump(methods, fp, indent=1)
    
    return methods


def generate_pyi(methods_json):

    types_dict = {
        "int": "int",
        "str": "str",
        "double": "float",
        "float": "float",
        "bool": "bool",
        "cimgui.bool": "bool",
        "cimgui.ImGuiCond" : "int",
        "cimgui.ImGuiTreeNodeFlags" : "int",
        "cimgui.ImU32": "int"
    }
    
    
    static_methods = list(filter(lambda x: x["class"]== "static", methods_json))

    member_methods  = sorted(list(filter(lambda x: x["class"] != "static", methods_json)), key=lambda x: x["class"])

    #pattern = r"(def|cdef|cpdef) ([a-z0-9]+(_[a-z0-9]+)*)\(((.+ .+(,\s?)?)+)?\)"
    pattern = r"(def|cdef|cpdef) (_?[a-z0-9]+(_[a-z0-9]+)*)\((self|((.+ .+(,\s?)?)+)?)\)"

    res = ["from typing import Any\n\n"]
    
    for m in static_methods:

        matches = re.finditer(pattern, m["fun"])

        if matches is not None:
            for k in matches:
                m_name = k.group(2)

                params_str = k.group(4)
                py_params = []
                if params_str is not None:
                    if "#" in params_str:
                        continue
                    params = params_str.split(",")

                    for p in params:
                        
                        default_val = None
                        p = p.strip()
                        p = p.replace(" =", "=").replace("= ", "=")

                        if p.count(" ") >= 1:
                            # print(p)
                            first_space_idx = p.find(" ")
                            p_type = p[0:first_space_idx]
                            p_name = p[first_space_idx:]
                            if "=" in p_name:
                                default_val = p_name.split("=")[1]
                                p_name = p_name.split("=")[0]

                            if types_dict.get(p_type) is None:
                                p_type = "Any"
                            else:
                                p_type = types_dict.get(p_type) 

                            if default_val is not None:
                                py_params.append(p_name + ": " +p_type + " = " + default_val )
                                default_val = None
                            else:
                                py_params.append(p_name + ": " +p_type)
                        else:
                            if "=" in p:
                                default_val = p.split("=")[1]
                                p_name = p.split("=")[0]
                                if default_val.isdigit() and "." not in default_val:
                                    p_type = "int"
                                elif default_val.isnumeric():
                                    p_type = "float"
                                else:
                                    p_type = "Any"
                            if default_val is not None:
                                py_params.append(p_name + ": " + p_type + " = " + default_val )
                                default_val = None
                            else:
                                py_params.append(p) #  + ": Any "
                
                res.append("def " + m_name + "(" + ",".join(py_params) + ") -> Any: ...\n")


    curr_class = ""
    classes_funcs = {}
    for m in member_methods:
        
        matches = re.finditer(pattern, m["fun"])

        if m["class"] != curr_class:
            #res.append("\n\nclass " + m["class"] + "(object):\n")
            curr_class = m["class"]
            if classes_funcs.get(curr_class) is None:
                classes_funcs[curr_class] = []
            
        if matches is not None:
            for k in matches:
                
                m_name = k.group(2)

                params_str = k.group(4)
                py_params = []
                if params_str is not None:
                    if "#" in params_str:
                        continue
                    params = params_str.split(",")

                    for p in params:
                        
                        default_val = None
                        p = p.strip()
                        p = p.replace(" =", "=").replace("= ", "=")

                        if p.count(" ") >= 1:
                            # print(p)
                            first_space_idx = p.find(" ")
                            p_type = p[0:first_space_idx]
                            p_name = p[first_space_idx:]
                            if "=" in p_name:
                                default_val = p_name.split("=")[1]
                                p_name = p_name.split("=")[0]

                            if types_dict.get(p_type) is None:
                                p_type = "Any"
                            else:
                                p_type = types_dict.get(p_type) 

                            if default_val is not None:
                                py_params.append(p_name + ": " +p_type + " = " + default_val )
                                default_val = None
                            else:
                                py_params.append(p_name + ": " +p_type)
                        else:
                            if "=" in p:
                                default_val = p.split("=")[1]
                                p_name = p.split("=")[0]
                                if default_val.isdigit() and "." not in default_val:
                                    p_type = "int"
                                elif default_val.isnumeric():
                                    p_type = "float"
                                else:
                                    p_type = "Any"
                            if default_val is not None:
                                py_params.append(p_name + ": " + p_type + " = " + default_val )
                                default_val = None
                            else:
                                py_params.append(p) #  + ": Any "
                classes_funcs[curr_class].append("\tdef " + m_name + "(" + ",".join(py_params) + ") -> Any: ...")
                #res.append("\tdef " + m_name + "(" + ",".join(py_params) + ") -> Any: ...\n")

    for _class in classes_funcs:
        
        res.append("\n\nclass " + _class + "(object):\n")

        if len(classes_funcs[_class]) == 0:
            res.append("\tpass")
        else:
            funcs = "\n".join(classes_funcs[_class])
            res.append(funcs)
    
    with open("imgui.pyi", "w") as fp:
        fp.writelines(res)


def extract(pyx_file,):
    methods = extract_methods(pyx_file)
    generate_pyi(methods)

if __name__ == "__main__":

    extract(sys.argv[1])