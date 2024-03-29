from __base__ import *  # ~~~ automatically generated by __autoinject__.py ~~~

from typing import List, Optional, Tuple

import tensorflow as tf

from errors import ModelTrainingError


class WeightRef:
    index: Optional[int] = None
    name: str
    shape: Optional[Tuple[int, ...]] = None
    __ref_global_weights_vec: Optional[List[tf.Variable]] = None

    def __init__(self, name: str):
        self.name = name

    def format_value(self, shape: Optional[Tuple[int, ...]]):
        if self.shape is None:  # TODO: None is a valid Tensorflow shape type: represents scalar values (fix this)
            self.shape = shape
        else:
            raise ModelTrainingError(msg="", code=ModelTrainingError.WEIGHT_VALUE_FORMATTED_TWICE)

    def activate(self, global_weights_vec: Optional[List[tf.Variable]]):
        """
        Makes the weight usable when training after adding the weight references to the global weight vector
        of the ModelTrainer class.
        """
        global_weights_vec.append(tf.Variable(tf.constant(0.0, shape=self.shape)))
        self.index = len(global_weights_vec)-1
        self.__ref_global_weights_vec = global_weights_vec

    def activate_set(self, global_weights_vec: Optional[List[tf.Variable]], index: int):
        """
        Connects the weight in the node to the global weights vector to be used (i.e. opposite of activate())
        """
        self.index = index
        self.__ref_global_weights_vec = global_weights_vec

    @property
    def value(self):
        if self.__ref_global_weights_vec is None:
            raise ModelTrainingError(msg="", code=ModelTrainingError.WEIGHT_REF_NOT_ACTIVATED)
        return self.__ref_global_weights_vec[self.index]

    def reset(self):
        self.index = None
        self.shape = None
        self.__ref_global_weights_vec = None


class NodeWeights:
    """
    Each new WeightRef object passed into the NodeWeights, it will create a new indexes using the name
    of such weights to improve readability.
    """

    def __init__(self, *weight_refs: WeightRef):
        self.collection: List[WeightRef] = []

        for wr in weight_refs:
            if isinstance(wr, WeightRef):
                if wr.name not in map(lambda w: w.name, self.collection):
                    self.collection.append(wr)
                else:
                    raise NameError(f"<{wr.name}> already exists in the collection")
            else:
                raise TypeError("invalid type in the collection")

    def __getitem__(self, item: str) -> WeightRef:
        if isinstance(item, str):
            for wr in self.collection:
                if wr.name == item:
                    return wr
            raise ValueError(f"<{item}> does not exist in the current NodeWeights")
        else:
            raise TypeError("invalid index type... must be string")

    def __len__(self):
        return len(self.collection)

    def reset(self):
        for w in self.collection:
            w.reset()
