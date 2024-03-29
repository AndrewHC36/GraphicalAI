from PySide6.QtWidgets import QGraphicsScene
from enum import Enum

import pandas as pd

from model_view.node import *
from model_view.components import *
from node_graph.backend import *
from errors import ModelExecutionRuntimeError


class NodeState(Enum):
    INPUT = 1
    OUTPUT = 2
    MEDIUM = 3


class NodeExec:
    ndtg = None  # node tag for internal representation; must have 5 characters in length
    name = None  # node name
    state = None  # node state {INPUT, OUTPUT, MEDIUM}

    def __init__(self):
        # values for each field at runtime
        # these intermediate variables are so it is easier to analyze errors and visualization
        self.inp = {}
        self.out = {}
        self.const = {}
        self.field_data = self._field_data()

    def interface(self, scene: QGraphicsScene, pos: tuple) -> FasterNode:
        """
        the GUI frontend code of the nodes
        """
        return FasterNode(scene, self, self.field_data, pos=pos)

    @staticmethod
    def _field_data():
        """
        returns pure field data for the nodes (must be at runtime since the QtWidget obj require a parent at runtime)
        """
        raise NotImplementedError()

    def execute(self, inst):
        """
        the node's execution supplied with necessary inputs, outputs, constants, and project instance state.
        """
        raise NotImplementedError()

    def descriptor(self):
        raise NotImplementedError()


class InputDataND(NodeExec):
    ndtg = "InpDT"
    name = "Input Data"
    state = NodeState.INPUT

    @staticmethod
    def _field_data(): return {
            "input": {"inp field A": CT.T_ANY},
            "output": {"out field A": CT.T_ANY, "out field B": CT.T_ANY},
            "constant": {"const field A": ComboBox(["F", "Xssss"])},
        }

    def execute(self, inst):
        print("EXECUTE!!!", self.inp, self.out, self.const, inst)


class OutputDataND(NodeExec):
    ndtg = "OutDT"
    name = "Output Data"
    state = NodeState.OUTPUT

    @staticmethod
    def _field_data(): return {
            "input": {"inp field A": CT.T_ANY},
            "output": {"out field A": CT.T_ANY, "out field B": CT.T_ANY},
            "constant": {"const field A": ComboBox(["Vrrr", "X"])},
        }

    def execute(self, inst):
        print("EXECUTE!!!", self.inp, self.out, self.const, inst)


class InputCSV(NodeExec):
    ndtg = "InpCV"
    name = "Input CSV"
    state = NodeState.INPUT

    @staticmethod
    def _field_data(): return {
            "input": {},
            "output": {"x": CT.T_ANY, "y": CT.T_ANY},
            "constant": {"fname": LineInput("filename"), "has depn. var": CheckBox(default=True), "dependent var": LineInput("")}
        }

    def execute(self, inst):
        print("input execution")
        df = pd.read_csv(self.const["fname"])
        print("???", self.const["has depn. var"])
        if self.const["has depn. var"]:
            y = df[self.const["dependent var"]]
            ydt = y.map(
                {k: v for (v, k) in enumerate(y.unique().tolist())}
            ).to_numpy()

            x = df.drop(self.const["dependent var"], axis=1)
            xdt = x.to_numpy()

            self.out["x"] = xdt
            self.out["y"] = ydt
        else:
            xdt = df.to_numpy()
            self.out["x"] = xdt
            self.out["y"] = None


class OutputCSV(NodeExec):
    ndtg = "OutCV"
    name = "Output CSV"
    state = NodeState.OUTPUT

    @staticmethod
    def _field_data(): return {
            "input": {"data": CT.T_ANY},
            "output": {},
            "constant": {"fname": LineInput("filename")}
        }

    def execute(self, inst):
        print("output execution")

        with open(self.const["fname"], "w") as fbo:
            fbo.write(str(self.inp["data"]))


class TrainMDL(NodeExec):
    ndtg = "TRMDL"
    name = "Train Model"
    state = NodeState.MEDIUM

    @staticmethod
    def _field_data(): return {
            "input": {"model": CT.T_ANY, "y": CT.T_ANY, "test": CT.T_ANY},
            "output": {"result": CT.T_ANY},
            "constant": {"epochs": IntLineInput(100), "rate": LineInput(str(0.01))}
        }

    def execute(self, inst):
        print("training execution")

        try:
            print("~~~", self.const["rate"])
            res = float(self.const["rate"])
        except ValueError:
            raise ModelExecutionRuntimeError(msg="", code=ModelExecutionRuntimeError.ERROR)

        self.inp["model"][0].train(self.inp["model"][1], self.inp["y"], self.const["epochs"], learning_rate=res)

        self.out["result"] = self.inp["model"][0].pred(self.inp["test"])


class LinearRegressionMDL(NodeExec):
    ndtg = "LRMDL"
    name = "Linear Regression"
    state = NodeState.MEDIUM

    @staticmethod
    def _field_data(): return {
            "input": {"x": CT.T_ANY},
            "output": {"result": CT.T_ANY},
            "constant": {}
        }

    def execute(self, inst):
        print("linear regression execution")
        print(len(self.inp["x"]), len(self.inp["x"][0]))
        linreg = ModelLinearReg(4)

        # linreg.train(self.inp["data"][0], self.inp["data"][1], 50)
        self.out["result"] = (linreg, self.inp["x"])


class LogisticRegressionMDL(NodeExec):
    ndtg = "LGMDL"
    name = "Logistic Regression"
    state = NodeState.MEDIUM

    @staticmethod
    def _field_data(): return {
            "input": {"data": CT.T_ANY},
            "output": {"result": CT.T_ANY},
            "constant": {}
        }

    def execute(self, inst):
        print("linear regression execution")
        linreg = ModelLogisticReg()  # TODO: add multiple independent variables

        # linreg.train(self.inp["data"][0], self.inp["data"][1], 50)
        # self.out["result"] = (linreg.bias, linreg.coef)


class _TESTND_LongConst(NodeExec):
    ndtg = "XXXX0"
    name = "Testing Long Const"
    state = NodeState.MEDIUM

    @staticmethod
    def _field_data(): return {
            "input": {"inp field A": CT.T_ANY, "inp field B": CT.T_ANY, "inp field C": CT.T_ANY},
            "output": {"out field A": CT.T_ANY, "out field B": CT.T_ANY},
            "constant": {"const field A": ComboBox(["None"]), "const field B": LineInput("default?"),
                         "const field C": ComboBox(["None"]), "const field D": LineInput("")},
        }

    def execute(self, inst):
        print("EXECUTE!!!", self.inp, self.out, self.const, inst)


class _TESTND_AllConst(NodeExec):
    ndtg = "XXXX1"
    name = "Testing All Const"
    state = NodeState.MEDIUM

    @staticmethod
    def _field_data(): return {
            "input": {"inp field A": CT.T_ANY, "inp field B": CT.T_ANY, "inp field C": CT.T_ANY},
            "output": {"out field A": CT.T_ANY, "out field B": CT.T_ANY},
            "constant": {"const field A": IntLineInput(40), "const field B": LineInput("texxt"),
                         "const field C": ComboBox(["a", "b", "c"]), "CHECKKKK BOX----": CheckBox(),
                         "var selc": VariableSelector(), "multibox": MultiComboBox()},
    }

    def execute(self, inst):
        print("EXECUTE!!!", self.inp, self.out, self.const, inst)



export = {
    "core": {
        "input data": InputDataND,
        "output data": OutputDataND,
        "T input csv": InputCSV,
        "T output csv": OutputCSV,
        "T training model": TrainMDL,
        "T linear regression": LinearRegressionMDL,
    },
    "single": {
    },
    "neural network": {
    },
    "old": {
        "long const": _TESTND_LongConst,
        "all const": _TESTND_AllConst,
    }
}

__nd_cls = {i: export[s][i] for s in export for i in export[s]}
node_class_ref = {__nd_cls[c].ndtg: __nd_cls[c] for c in __nd_cls}
