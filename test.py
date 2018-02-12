from sklearn import tree
from sklearn import svm
from sklearn import preprocessing

import numpy as np
import re


class Classifier(object):
    def __init__(self):
        super().__init__()
        self._runpath = '.'

        self._clf = tree.DecisionTreeClassifier()
        # self._clf = svm.SVC()

        self._abbrvs = set()
        self._titles = set()
        self._initialize_set()

        self._features = []
        self._labels = []

    def _initialize_set(self):
        with open(self._runpath + '/classes/abbrevs') as f:
            for line in f:
                self._abbrvs.add(line)
        with open(self._runpath + '/classes/titles') as f:
            for line in f:
                self._titles.add(line)

    def _initialize_data(self, filename):
        with open(self._runpath + '/' + filename) as f:
            for line in f:
                line_arr = line.split()
                self._features.append(self._get_features(line_arr[4:]))
                self._labels.append(line_arr[0])

    def _get_features(self, arr):
        ret = []
        # Rule No.1, if the next word starts with a lower case letter, it should not be an EOS.
        ret.append(-1 if re.match(r'^[a-z]', arr[2]) else 0)
        # Rule No.2, if the next word is a paragraphy indicator, it should be an EOS.
        ret.append(1 if re.match(r'^<P>', arr[2]) else 0)
        # Rule No.3, if the next word is some specific punctuation mark, it should not be an EOS.
        ret.append(-1 if re.match(r'^[.,?!;]', arr[2]) else 0)
        # Rule
        # Rule No.4, if the prev word is a common title, is should not an EOS.
        ret.append(-1 if arr[0] in self._titles else 0)
        # Rule No.5, if the prev word is a common abbr, is should not an EOS.
        ret.append(-1 if arr[0] in self._abbrvs else 0)
        # ret.append(int(arr[5]))
        # ret.append(int(arr[6]))
        ret.append(1 if int(arr[7]) >= 2 else 0)

        return ret

    def _train(self):
        self._clf.fit(self._features, self._labels)

    def _test(self):
        cc = 0
        for i in range(0, 45000):
            if self._clf.predict([self._features[i]])[0] == self._labels[i]:
                cc += 1
        print(cc/45000.0)


if __name__ == '__main__':
    clf = Classifier()
    clf._initialize_set()
    clf._initialize_data('sent.data.train')
    clf._train()
    clf._test()

