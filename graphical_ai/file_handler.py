import os
import yaml

from errors import *
from node_graph.execution import ModelExecutor
from node_graph.nodes import node_class_ref


class ReferencedFileHandler:
    """
    Used to load previous loaded projects or project executables to the homepage as a convenience to resume whatever
    the user has been working on previous projects. (Assuming the path to the project remains valid; if not, it will
    display the project name in red color)
    """
    FILE_LOC = ".\\proj_ref.yaml"

    def __init__(self):
        if os.path.isfile(self.FILE_LOC):
            with open(self.FILE_LOC, "r") as fbo:
                fdt = fbo.read()
                self.refs = yaml.safe_load(fdt)
                if self.refs is None:  # if yaml parser returns none
                    self.refs = {"proj": {}, "exec-proj": {}}
        else:  # if file does not exist
            self.refs = {"proj": {}, "exec-proj": {}}
        print(self.refs)

    def save(self):
        with open(self.FILE_LOC, "w") as fbo:
            fbo.write(yaml.dump(self.refs))

    def loaded_projects(self) -> list:
        loaded = [(v_name, k_path, os.path.exists(k_path)) for (k_path, v_name) in self.refs["proj"].items()]
        return loaded

    def loaded_exec_projects(self) -> list:
        loaded = [(v_name, k_path, os.path.exists(k_path)) for (k_path, v_name) in self.refs["exec-proj"].items()]
        return loaded

    def ref_proj_existed(self,
                         path: str) -> bool:  # returns whether the specified path is already referenced for project
        return path in self.refs["proj"]

    def ref_exec_proj_existed(self,
                              path: str) -> bool:  # returns whether the specified path is already referenced for exec project
        return path in self.refs["exec-proj"]

    def add_project(self, name: str, root_file: str):  # add project to the reference
        # note: path str should be in full path
        self.refs["proj"][root_file] = name

    def rem_project(self, root_file: str):  # remove project from the reference
        if root_file in self.refs["proj"]:
            del self.refs["proj"][root_file]
        else:
            print(f"error: the project file path reference <{root_file}> was not found")

    # TODO: executable project might not have root_files
    def add_exec_project(self, name: str, root_file: str):  # add exec project to the reference
        # note: path str should be in full path
        self.refs["exec-proj"][root_file] = name

    def rem_exec_project(self, root_file: str):  # remove exec project from the reference
        if root_file in self.refs["exec-proj"]:
            del self.refs["exec-proj"][root_file]
        else:
            print(f"error: the exec project file path reference <{root_file}> was not found")


class ProjectFileHandler:
    """
    Used to load files from the project directory to the workspace.
    """

    def __init__(self, root_file, path, dat, models, exec_models):
        self.path = path
        self.name = dat["name"]
        self.root_file = root_file
        self.root = os.path.join(path, self.name)
        self.dat = dat
        self.models: dict = models  # dict of model data (dict of dict {mdl_id:{mdl_data}})
        self.exec_models: dict = exec_models  # dict of model data ready to be executed in project

        # self.gem_models: dict = models  # dict of model data ready to be executed independently

    @classmethod
    def create_project(cls, path: str, name: str):
        print("creating project")

        dat = {
            "version": 0,  # file version
            "writes": 0,  # how many times the project file has been saved, since last project path changed
            "reads": 0,  # how many times the project file has been loaded, since last project path changed
            "name": name,
            "mdl_id_counter": 0,
            "mdl_ids": {},  # {mdl_id: mdl_name}
        }

        models = {}  # model datas are stored in here
        exec_models = {}

        return cls(None, path, dat, models, exec_models)

    @classmethod
    def load_project(cls, root_file):
        print("loading project")

        from node_graph.nodes import node_class_ref

        # load project method has an file check exist requirement because it will be immediately be read
        if not os.path.isfile(root_file):
            raise ProjectFileAppError(msg="", code=ProjectFileAppError.PROJ_FILE_DOESNT_EXIST)

        (root, _fname) = os.path.split(root_file)

        MODELS_PATH = os.path.join(root, "models")
        RESOURCES_PATH = os.path.join(root, "resources")

        with open(root_file, "r") as fbo:
            fdt = fbo.read()
            dat = yaml.safe_load(fdt)

        dat["reads"] += 1

        models = {}
        exec_models = {}

        ref_mdl_id = {v: k for k, v in dat["mdl_ids"].items()}
        _COLLC_SIZE = 1
        NDTG_LEN = 5
        _COLLC_SIZE = 1
        _CONST_COLLC_SIZE = 2
        _NODE_SIZE = 3  # byte size for the length of a single binary-serialized executable node data

        for mdl_file in os.listdir(MODELS_PATH):
            if mdl_file.endswith(".mdl.yaml"):
                print(f"loading model data <{mdl_file}>")
                with open(os.path.join(MODELS_PATH, mdl_file), "r") as fbo:
                    fdt = fbo.read()
                    mdl_dat = yaml.safe_load(fdt)
                mdl_name = mdl_file[:-len(".mdl.yaml")]
                try:
                    models[ref_mdl_id[mdl_name]] = mdl_dat
                except KeyError:
                    raise ProjectFileAppError(msg="", code=ProjectFileAppError.MDL_NAME_NON_EXISTENT)
            elif mdl_file.endswith(".gem"):
                print(f"loading executable model data <{mdl_file}>")
                model_exec_data = []
                with open(os.path.join(MODELS_PATH, mdl_file), "rb") as fbo:
                    fdt_raw = fbo.read()
                    fdt = []
                    # meta-processing file data to a processed raw file data
                    fdt.append(fdt_raw[0:6])
                    fdt.append(fdt_raw[6:8])

                    mmode = "size"  # meta-mode
                    size = 0
                    sbuf = b""
                    fbuf = b""
                    for ci in range(8, len(fdt_raw)):
                        if len(sbuf) == _NODE_SIZE and mmode == "size":
                            size = int.from_bytes(sbuf, "big")
                            mmode = "node-data"
                            fbuf = fdt_raw[ci:ci+1]
                        elif len(fbuf) == size and mmode == "node-data":
                            fdt.append(fbuf)
                            mmode = "size"
                            size = 0
                            sbuf = fdt_raw[ci:ci+1]
                            fbuf = b""
                        elif ci == len(fdt_raw)-1 and mmode == "node-data":
                            fbuf += fdt_raw[ci:ci + 1]
                            fdt.append(fbuf)
                        elif mmode == "size":
                            sbuf += fdt_raw[ci:ci+1]
                        else:
                            fbuf += fdt_raw[ci:ci+1]

                    # print(fdt)
                    mdl_name = mdl_file[:-len(".gem")]
                    if fdt[0][0:3] != b"SHC" or len(fdt) <= 2:
                        raise ProjectFileAppError(msg="", code=ProjectFileAppError.FILE_GEM_INVALID)
                    nddt = fdt[2:]
                    #TODO: implement file type and version check and version conversion
                    #TODO: beware of newline character as part of the binary data, think of a better separator character
                    # a possible solution is to state the length of a line of node data through 4 bytes
                    FTYPE = fdt[0][3]
                    VERSN = fdt[0][4]
                    ID_SZ = fdt[1][0]

                    for nd in nddt:
                        ndnm = nd[0:NDTG_LEN].decode("ASCII")
                        inp_size = None
                        out_size = None
                        const_size = None
                        # input fields stores all of its input field id
                        # output fields only stores an array of referenced inp field's id
                        fld_inp = []
                        fld_out = [-1]  # will be read as index -1 after first append; only here bc IndexError
                        tmp_out_refs = []
                        fld_const = [-1]  # will be read as index -1 after first append; only here bc IndexError

                        cbuf = b""
                        mode = "sizes"
                        for i in range(NDTG_LEN, NDTG_LEN+len(nd[NDTG_LEN:])):
                            if len(cbuf) == _COLLC_SIZE and mode == "sizes":
                                if inp_size is None:
                                    inp_size = int.from_bytes(cbuf, "big")
                                elif out_size is None:
                                    out_size = int.from_bytes(cbuf, "big")
                                elif const_size is None:
                                    const_size = int.from_bytes(cbuf, "big")
                                    # print("SIZES BEF", inp_size, out_size, const_size)
                                    if inp_size > 0:
                                        mode = "inp"
                                    elif out_size > 0:
                                        mode = "ref_sizes"
                                    elif const_size > 0:
                                        mode = "const_dt_sizes"
                                    else:
                                        mode = None

                                cbuf = nd[i:i+1]
                            elif len(cbuf) == ID_SZ and mode == "inp":
                                if inp_size > 1:
                                    fld_inp.append(int.from_bytes(cbuf, "big"))
                                    inp_size -= 1
                                else:
                                    fld_inp.append(int.from_bytes(cbuf, "big"))

                                    if out_size > 0: mode = "ref_sizes"
                                    elif const_size > 0: mode = "const_dt_sizes"
                                    else: mode = None
                                cbuf = nd[i:i + 1]
                            elif len(cbuf) == _COLLC_SIZE and mode == "ref_sizes":  # getting the length of the ref inps
                                # there will always be an integer in the fld_out list to signify its size before
                                # it properly converts into a further subarray of connected referenced inputs within a
                                # single output connector
                                if out_size > 0:
                                    ref_size = int.from_bytes(cbuf, "big")
                                    out_size -= 1
                                    if ref_size > 0:
                                        fld_out.append(int.from_bytes(cbuf, "big"))
                                        mode = "out"
                                    else:
                                        fld_out.append([])
                                    cbuf = nd[i:i + 1]
                                else:
                                    mode = "const_dt_sizes"
                                    cbuf += nd[i:i+1]
                            elif len(cbuf) == ID_SZ and mode == "out":  # reads each input id referenced from one out
                                if fld_out[-1] > 1:
                                    tmp_out_refs.append(int.from_bytes(cbuf, "big"))
                                    fld_out[-1] -= 1
                                elif fld_out[-1] == 1:
                                    tmp_out_refs.append(int.from_bytes(cbuf, "big"))
                                    fld_out[-1] = tmp_out_refs.copy()
                                    tmp_out_refs.clear()

                                if out_size != 0 and type(fld_out[-1]) == list: mode = "ref_sizes"
                                elif out_size == 0 and type(fld_out[-1]) == list: mode = "const_dt_sizes"
                                cbuf = nd[i:i + 1]
                            elif len(cbuf) == _CONST_COLLC_SIZE and mode == "const_dt_sizes":
                                # there will always be an integer in the fld_out list to signify its size before
                                # it properly converts into a further subarray of connected referenced inputs within a
                                # single output connector
                                fld_const.append(int.from_bytes(cbuf, "big"))
                                mode = "const"
                                cbuf = nd[i:i+1]
                            elif len(cbuf) == fld_const[-1] and mode == "const":
                                fld_const[-1] = cbuf
                                if const_size > 0: mode = "const_dt_sizes"
                                else: mode = None  # end
                                cbuf = nd[i:i+1]
                            elif fld_const[-1] == 0 and mode == "const":
                                del fld_const[-1]
                                if const_size > 0: mode = "const_dt_sizes"
                                else: mode = None  # end
                                cbuf += nd[i:i+1]
                            else:
                                cbuf += nd[i:i+1]
                        node_exec_dt = {}
                        node_exec_dt["ndtg"] = ndnm
                        node_exec_dt["inp"] = fld_inp
                        node_exec_dt["out"] = fld_out[1:]
                        # TODO: optimization: maybe directly set the object instead of trashing the field data
                        node_exec_dt["const"] = {name:val for (name, val) in zip(node_class_ref[ndnm]().field_data["constant"], fld_const[1:])}
                        model_exec_data.append(node_exec_dt)
                print(f"loading project <{ref_mdl_id[mdl_name]}>: model-exec data", model_exec_data)
                exec_models[ref_mdl_id[mdl_name]] = model_exec_data

        return cls(root_file, os.path.split(root)[0], dat, models, exec_models)

    def save_project(self):
        print("saving project")

        MODELS_PATH = os.path.join(self.root, "models")
        RESOURCES_PATH = os.path.join(self.root, "resources")

        if self.dat["writes"] == 0:
            try:
                os.mkdir(os.path.join(self.root))
            except FileExistsError:
                raise ProjectFileAppError(msg="", code=ProjectFileAppError.PROJ_CREATION_DIR_EXIST)

        if self.dat["writes"] == 0:
            os.mkdir(MODELS_PATH)
            os.mkdir(RESOURCES_PATH)

        if self.root_file is None:
            self.root_file = os.path.join(self.root, "project.yaml")

        with open(self.root_file, "w") as fbo:
            self.dat["writes"] += 1
            fbo.write(yaml.dump(self.dat))

        for mdl_id in self.models:
            with open(os.path.join(MODELS_PATH, f"{self.dat['mdl_ids'][mdl_id]}.mdl.yaml"), "w") as fbo:
                fbo.write(yaml.dump(self.models[mdl_id]))

        EMDL_FTYPE = 0x10
        GEM_FVERS = 0x01
        GEM_UIDSIZE = 1  # byte size for UID
        _COLLC_SIZE = 1  # private variable for common default byte size for collection lengths
        _CONST_COLLC_SIZE = 2
        _NODE_SIZE = 3  # byte size for the length of a single binary-serialized executable node data

        for mdl_id in self.exec_models:
            fdt = []
            fdt.append(bytearray([ord("S"), ord("H"), ord("C"), EMDL_FTYPE, GEM_FVERS, ord("\n")]))  # magic word, file type, file type version
            fdt.append(bytearray([GEM_UIDSIZE, ord("\n")]))

            for node in self.exec_models[mdl_id]:
                node_bdt = bytearray()

                # print("node:", node)
                # print("node indv exec data:",
                #       node["ndtg"],
                #       len(node["inp"]).to_bytes(_COLLC_SIZE, "big"),
                #       len(node["out"]).to_bytes(_COLLC_SIZE, "big"),
                #       len(node["const"]).to_bytes(_COLLC_SIZE, "big"),
                #       b"".join([uid.to_bytes(GEM_UIDSIZE, "big") for uid in node["inp"]]),
                #       b"".join([(len(i).to_bytes(_COLLC_SIZE, "big")+b"".join([uid.to_bytes(GEM_UIDSIZE, "big") for uid in i])) for i in node["out"]]),
                #       b"".join([(len(node["const"][i]).to_bytes(2, "big")+node["const"][i]) for i in node["const"]]))

                node_bdt.extend(node["ndtg"].encode("ASCII"))
                node_bdt.extend(len(node["inp"]).to_bytes(_COLLC_SIZE, "big"))
                node_bdt.extend(len(node["out"]).to_bytes(_COLLC_SIZE, "big"))
                node_bdt.extend(len(node["const"]).to_bytes(_COLLC_SIZE, "big"))
                node_bdt.extend(b"".join([uid.to_bytes(GEM_UIDSIZE, "big") for uid in node["inp"]]))
                node_bdt.extend(b"".join(
                    [(len(i).to_bytes(_COLLC_SIZE, "big")+b"".join([uid.to_bytes(GEM_UIDSIZE, "big") for uid in i]))
                     for i in node["out"]])
                )
                # TODO: optimization: maybe using the optimization from earlier, and directly use the "cached" fld data
                nd_const_ordered = node_class_ref[node["ndtg"]]._field_data()["constant"]
                # using nd_const_ordered instead of directly iterating through the constant ordered from the node dict,
                # because using field data's order of the constant provides standardization of the ordering of the dict
                node_bdt.extend(b"".join(
                    [(len(node["const"][i]).to_bytes(_CONST_COLLC_SIZE, "big")+node["const"][i]) for i in nd_const_ordered])
                )
                node_bdt.extend(b"\n")
                node_bdt = bytearray(len(node_bdt).to_bytes(_NODE_SIZE, "big"))+node_bdt
                fdt.append(node_bdt)

            with open(os.path.join(MODELS_PATH, f"{self.dat['mdl_ids'][mdl_id]}.gem"), "wb") as fbo:
                fbo.writelines(fdt)

    def load_model(self, mdl_id: int, parent=None):
        if not self._valid_model_id(mdl_id): raise ProjectFileAppError(msg="", code=ProjectFileAppError.MDL_ID_INVALID)

        from PySide6.QtCore import QPointF
        from project.model_editor import ModelWorkspace
        from model_view.node import FasterNode
        from model_view.connection import Connection
        from model_view.components import InteractiveComponent
        from node_graph.nodes import NodeExec, node_class_ref

        print(f"loading model <{mdl_id}:{self.dat['mdl_ids'][mdl_id]}>")

        model_wkrspc = ModelWorkspace(self.dat["mdl_ids"][mdl_id], parent=parent)
        exec_node_dt = []

        dto = self.models[mdl_id].copy()
        cids = list(self.models[mdl_id].keys())
        cids.reverse()

        # converts connection and interactive components concrete data into python objects
        for cid in cids:
            compn = dto[cid]
            if "connection" in compn:  # connection
                dto[cid] = Connection(QPointF(0, 0), QPointF(0, 0))
                model_wkrspc.qscene.addItem(dto[cid])
            elif "ctag" in compn:  # interactive components
                dto[cid] = compn["cdat"]

        # converts node data into python objects, and modify them from connector, connection, and interactive-compn info
        for cid in cids:
            compn = dto[cid]
            if not isinstance(compn, dict):
                continue
            if "tag" in compn:  # node
                node: NodeExec = node_class_ref[compn["tag"]]()
                exec_node_dt.append(node)
                wx_node: FasterNode = node.interface(model_wkrspc.qscene, (0,0))
                wx_node.setPos(QPointF(compn["pos"][0], compn["pos"][1]))

                # and then we add the connections to each of the connectors
                for i in range(0, len(wx_node.fd_input)):
                    wx_node.connectors[i].prim_connc = [dto[c] for c in dto[compn["connc"][i]]["pc"]]
                    wx_node.connectors[i].scnd_connc = [dto[c] for c in dto[compn["connc"][i]]["sc"]]
                for i in range(len(wx_node.fd_input), len(wx_node.fd_input) + len(wx_node.fd_output)):
                    wx_node.connectors[i].prim_connc = [dto[c] for c in dto[compn["connc"][i]]["pc"]]
                    wx_node.connectors[i].scnd_connc = [dto[c] for c in dto[compn["connc"][i]]["sc"]]

                # update the state of constant fields
                c: InteractiveComponent
                for ind, c in enumerate(wx_node.fd_wx_consts):
                    c.deserialize(dto[compn["const"][ind]])

                model_wkrspc.qscene.addItem(wx_node)
                wx_node.update_connc()
                wx_node.add_const_wx(model_wkrspc.qscene)

        return model_wkrspc

    def save_model(self, mdl_id: int, model):
        if not self._valid_model_id(mdl_id): raise ProjectFileAppError(msg="", code=ProjectFileAppError.MDL_ID_INVALID)

        from model_view.components import InteractiveComponent
        from model_view.connection import Connection
        from model_view.node import FasterNode, Connector, InputField, OutputField, ConstantField, CT

        print(f"saving model <{mdl_id}:{self.dat['mdl_ids'][mdl_id]}>")
        tmp_id_ref = {}
        tmp_id_ref_rev = {}
        mdl_dt = {}
        itm_id = 0

        # indexing object reference to the temporary id reference
        for o in model.scene().items():
            if isinstance(o, (InteractiveComponent, Connection, FasterNode, Connector)):
                tmp_id_ref[itm_id] = o
                tmp_id_ref_rev[o] = itm_id
                mdl_dt[itm_id] = {}
                itm_id += 1
        # print(mdl_dt)

        # then reads off the temporary id reference to locate the model data and fill up with concrete data
        for cid in mdl_dt:
            obj = tmp_id_ref[cid]
            dto = {}
            if isinstance(obj, FasterNode):
                dto["tag"] = obj.ndtg
                dto["pos"] = [obj.x(), obj.y()]
                dto["const"] = []
                dto["connc"] = []
                for wc in obj.fd_wx_consts:  # const widgets store in lists should be ordered
                    # print(tmp_id_ref_rev[wc], wc)
                    dto["const"].append(tmp_id_ref_rev[wc])
                for cn in obj.connectors:  # connectors list should be ordered
                    # print(tmp_id_ref_rev[cn], cn, cn.ct, cn.prim_connc, cn.scnd_connc)
                    dto["connc"].append(tmp_id_ref_rev[cn])
            elif isinstance(obj, Connection):
                dto["connection"] = None
            elif isinstance(obj, Connector):
                dto["ct"] = obj.ct
                dto["pc"] = [tmp_id_ref_rev[c] for c in obj.prim_connc]  # primary connections
                dto["sc"] = [tmp_id_ref_rev[c] for c in obj.scnd_connc]  # secondary connections
            elif isinstance(obj, InteractiveComponent):
                dto["ctag"] = obj.ctag
                dto["cdat"] = obj.serialize()
            mdl_dt[cid] = dto

        self.models[mdl_id] = mdl_dt

        print(f"saving executable model <{mdl_id}:{self.dat['mdl_ids'][mdl_id]}>")

        scene_itms = model.scene().items()
        mdl_exec_dt = []
        obj_ref_id = {i:(ind+1) for (ind, i) in
                      enumerate(filter( lambda obj: isinstance(obj, (FasterNode, Connection, Connector)), scene_itms ))}

        # maps connection object to all of its inputs (from output connectors POV)
        out_fld_refs = {}
        for connc_out in scene_itms:
            if isinstance(connc_out, Connector):
                if connc_out.ct & CT.OUTPUT == CT.OUTPUT:
                    out_fld_refs[obj_ref_id[connc_out]] = []
                    for connc_inp in scene_itms:
                        if isinstance(connc_inp, Connector):
                            if connc_inp.ct & CT.INPUT == CT.INPUT:
                                if len(set(connc_inp.prim_connc+connc_inp.scnd_connc) & set(connc_out.prim_connc+connc_out.scnd_connc)):
                                    # the input and output connector has at least one common connections
                                    out_fld_refs[obj_ref_id[connc_out]].append(obj_ref_id[connc_inp])

        for o in scene_itms:
            if isinstance(o, FasterNode):
                exec_ndt = {}
                exec_ndt["ndtg"] = o.ndtg
                exec_ndt["inp"] = []  # list of connector
                exec_ndt["out"] = []  # list of list of connector
                exec_ndt["const"] = {}  # dict of const name str to binary data

                connc: Connector
                for connc in o.connectors:
                    if connc.ct & CT.INPUT == CT.INPUT:
                        # input field should always have one connection (either its primary or secondary)
                        exec_ndt["inp"].append(obj_ref_id[connc])

                        if len(connc.prim_connc+connc.scnd_connc) > 1:
                            print(f"warning: node <{o}> has an input connector <{connc}> that exceeded with its max one connection limit")
                    elif connc.ct & CT.OUTPUT == CT.OUTPUT:
                        exec_ndt["out"].append(out_fld_refs[obj_ref_id[connc]])

                const_obj: ConstantField
                const_wx: InteractiveComponent
                for (const_obj, const_wx) in zip(o.fd_constant, o.fd_wx_consts):
                    exec_ndt["const"][const_obj.name] = const_wx.bin_serialize()

                mdl_exec_dt.append(exec_ndt)

        self.exec_models[mdl_id] = mdl_exec_dt

    def delete_model(self, mdl_id: int):
        if not self._valid_model_id(mdl_id): raise ProjectFileAppError(msg="", code=ProjectFileAppError.MDL_ID_INVALID)

        print(f"deleting model <{mdl_id}:{self.dat['mdl_ids'][mdl_id]}>")

    def execute_model(self, mdl_id: int):
        if not self._valid_model_id(mdl_id): raise ProjectFileAppError(msg="", code=ProjectFileAppError.MDL_ID_INVALID)

        print(f"executing model <{mdl_id}:{self.dat['mdl_ids'][mdl_id]}>")

        print("model exec data", self.exec_models[mdl_id])
        executor = ModelExecutor(self.exec_models[mdl_id])
        executor.execute(None)

    def get_mdl_refs(self) -> dict:
        return self.dat["mdl_ids"]

    def new_mdl_id(self, mdl_name: str) -> int:
        if mdl_name in self.dat["mdl_ids"].values():
            # if the specified mdl_name is already existed within the model id reference
            raise ProjectFileAppError(msg="", code=ProjectFileAppError.MDL_ID_GEN_DUPE_NAME)
        else:
            mdl_id = self.dat["mdl_id_counter"]
            self.dat["mdl_ids"][mdl_id] = mdl_name
            self.dat["mdl_id_counter"] += 1
            return mdl_id

    def get_mdl_id(self, mdl_name: str) -> int:
        inv_map = {v: k for k, v in self.dat["mdl_ids"].items()}
        if mdl_name in inv_map:
            return inv_map[mdl_name]
        else:
            # model name does not exist
            raise ProjectFileAppError(msg="", code=ProjectFileAppError.MDL_NAME_NON_EXISTENT)

    def change_mdl_name(self, mdl_id: int, mdl_name: str):
        if not self._valid_model_id(mdl_id): raise ProjectFileAppError(msg="", code=ProjectFileAppError.MDL_ID_INVALID)

        self.dat["mdl_ids"][mdl_id] = mdl_name

    def _valid_model_id(self, mdl_id: int):
        return mdl_id in self.dat["mdl_ids"]


class ProjectExecFileHandler:
    pass

# if __name__ == '__main__':
# 	fhndl = ProjectFileHandler.load_project(".\\name\\project.yaml")
# 	fhndl.save_project()
