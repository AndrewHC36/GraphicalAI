from node_graph.nodes import node_class_ref, NodeState
from errors import ModelExecutionRuntimeError, ModelExecutionError

import copy


class ModelExecutor():
    # TODO: executor will need info about variable selection, variable specifier, etc.

    def __init__(self, model_exec_data):
        # each individual nodes are labelled with an id based on its index in the model exec data list
        self.mdl_ref_dt = copy.deepcopy(model_exec_data)  # mapper between node-exec id and the actual node data
        self.inp_ref_nd = {}  # mapper between input id to its respective node (through node id) and its name
        self.node_anchors = []

        self.node_adj_list = {nid:[] for nid in range(0, len(self.mdl_ref_dt))}
        for (nid, nd) in enumerate(self.mdl_ref_dt):
            nd["%%class"] = node_class_ref[nd["ndtg"]]()
            # print(nd, nd["%%class"].state)
            # print(nid, nd["inp"])
            # print("zip?", nd["inp"], nd["%%class"].field_data()["input"])
            for (inp_id, inp_nm) in zip(nd["inp"], nd["%%class"].field_data["input"]):
                self.inp_ref_nd[inp_id] = (nid, inp_nm)
            for (out_nid, out_nd) in enumerate(self.mdl_ref_dt):
                out_fld = [j for i in out_nd["out"] for j in i]
                if len(nd["inp"]+out_fld) > len(set(nd["inp"]) | set(out_fld)):
                    self.node_adj_list[out_nid].append(nid)
            for const_nm in nd["const"]:
                nd["const"][const_nm] = nd["%%class"].field_data["constant"][const_nm].bin_deserialize(nd["const"][const_nm])
            if nd["%%class"].state == NodeState.INPUT:
                self.node_anchors.append(nid)
            # print("FIELD APPENDING", nd["inp"], nd["out"])
        # print(self.node_adj_list)

    def execute(self, instance):
        """
        executes the model node graph
        """
        print("model execution begin")

        # print("MAPPER", self.mdl_ref_dt)
        # print("INPREF", self.inp_ref_nd)
        # print("ANCHOR", self.node_anchors)
        # print("ADJLST", self.node_adj_list)

        # this is a modified breadth-first search where there are no visited queue, because first time you visit
        # Node A, it might not be ready till all the other connected nodes assigns the values to Node A's input.
        # In other words, calling the already visited Node A is OK, and once the last connected node refers to Node A,
        # then it will allow Node A to execute (because then all the Node A's inputs are assigned with values).

        queue = self.node_anchors.copy()
        while len(queue) != 0:
            print("===")

            first = queue[0]
            del queue[0]
            nd_dt = self.mdl_ref_dt[first]  # note: reference (not copy)
            fld_meta = nd_dt["%%class"].field_data

            for nd_ref in self.node_adj_list[first]:
                queue.append(nd_ref)

            # print("STATE:", nd_dt["%%class"].state)
            # print("FIELD:", fld_meta)
            # print("ND DT:", nd_dt)

            # per each node executed
            # ----------------------
            # 1. check all input field data is filled
            # 2. retrieve all the constant's value
            # 3. execute the node
            # 4. check output field data is valid
            #   ~ Are all necessary fields filled (else return a warning and fill that field with None)
            #   ~ Additional unknown fields will be sent out as a warning and break
            #   ~ [Tentative:TypeChecking] If that output field does not have a correct type (else return a warning)
            # 5. Find each output field's reference input field ID through the mapper to find the node
            # 6. Fill the referenced input field with the data from output
            # --- done ---

            if nd_dt["%%class"].state != NodeState.INPUT:
                # print("INP", nd_dt["%%class"].inp)
                valid_inp = True
                for ifld_nm in fld_meta["input"]:
                    if ifld_nm not in nd_dt["%%class"].inp:
                        valid_inp = False
                        break
                if valid_inp is False:
                    print("warning: incomplete input")
                    continue

            # NOTE: retrieving value directly from the constant widget object itself rather than deserializing
            #   binary data is not garunteed to have the same value as the user specified, as this class strives
            #   to be independent from node data. Only from the read binary data.
            nd_dt["%%class"].const = nd_dt["const"]  # {k:fld_meta["constant"][k].value() for k in fld_meta["constant"]}
            try:
                nd_dt["%%class"].execute(instance)
            except ModelExecutionRuntimeError as e:
                raise e
            except BaseException as e:
                raise ModelExecutionError(msg=e, code=ModelExecutionError.DEBUG_ERROR)

            if nd_dt["%%class"].state != NodeState.OUTPUT:
                # print("OUT", nd_dt["%%class"].out)
                for (ind, ofld_nm) in enumerate(fld_meta["output"]):
                    # each output field in this node
                    if ofld_nm not in nd_dt["%%class"].out:
                        print(f"warning: output field <{ofld_nm}> is missing; will be replaced with None")
                        nd_dt["%%class"].out[ofld_nm] = None
                    for inp_ref in nd_dt["out"][ind]:
                        # each referenced input of ext node of the individual output field in the current master node
                        ext_node = self.mdl_ref_dt[self.inp_ref_nd[inp_ref][0]]
                        ext_node["%%class"].inp[self.inp_ref_nd[inp_ref][1]] = nd_dt["%%class"].out[ofld_nm]
                # print(nd_dt["%%class"].out)

            # TODO: create a diagram why we do this instead of using visited list
            # this is it removes any additional occurrences of the current <first> node presently from the queue, as to
            # not repeat, while also allow loops with at least 2 different node instance it has to loop through
            # (or else it just directly refers back to the queue and get removed instantly and its unreadable
            # w/ a single node instance loop)
            queue = [n for n in queue if n != first]

        print("model execution finished")
