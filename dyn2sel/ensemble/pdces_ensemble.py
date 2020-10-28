from copy import deepcopy

import numpy as np
from dyn2sel.ensemble import Ensemble
from dyn2sel.ensemble._skmultiflow_encapsulator import skmultiflow_encapsulator
from dyn2sel.utils import BalancedAccuracyEvaluator
from skmultiflow.core import ClassifierMixin


class PDCESEnsemble(Ensemble):
    def __init__(self, clf, max_size=10):
        super().__init__()
        self.clf = clf
        self.max_size = max_size
        self.bac_ensemble = []

    def partial_fit(self, X, y, classes=None, sample_weight=None):
        self.update_bac(X, y)
        clf_copy = deepcopy(self.clf)
        if issubclass(type(clf_copy), ClassifierMixin):
            clf_copy = skmultiflow_encapsulator(clf_copy)
        clf_copy.partial_fit(X, y)
        if len(self.ensemble) >= self.max_size:
            self.del_member(self.get_worst_bac())
        self.add_member(clf_copy)

    def predict(self, X):
        predictions = np.empty((len(self.ensemble), X.shape[0]))
        for index_clf, clf in enumerate(self.ensemble):
            predictions[index_clf] = clf.predict(X)
        return predictions.T

    def predict_proba(self, X):
        pass

    def add_member(self, clf):
        self.ensemble.append(clf)
        self.bac_ensemble.append(BalancedAccuracyEvaluator())

    def del_member(self, index=-1):
        self.ensemble.pop(index)
        self.bac_ensemble.pop(index)

    def update_bac(self, X, y):
        for i in range(len(self.ensemble)):
            self.bac_ensemble[i].add_results(y, self.ensemble[i].predict(X))

    def get_worst_bac(self):
        return np.argmin([i.get_bac() for i in self.bac_ensemble])
