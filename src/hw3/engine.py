import re
import math
from collections import defaultdict

from constants import DataFile, Weight
from kNN import kNNHelper

RESOURCE_DIR = './assets'

class IREngine:

    def __init__(self):
        self.doc_vectors = []

        self.titles = []

        self.sense_num = [0]

        self.stop_list_hash = set()

        self.num_of_doc = 0

        self.word_position = [-1]


        print('NITIALIZING VECTORS ... ')
        self.datafile = DataFile(RESOURCE_DIR, True)

        self.init_corp_freq()

        self.num_of_doc = self.init_doc_vectors(self.datafile.perplace_docs, self.doc_vectors, self.sense_num)

    def init_corp_freq(self):
        with open(self.datafile.common_words, 'r') as f:
            for line in f:
                if line:
                    self.stop_list_hash.add(line.strip())

        self.titles.append('')
        with open(self.datafile.tank_docs, 'r') as f:
            for line in f:
                if line:
                    self.titles.append(line.strip())

    def init_word_position(self, file):
        with open(file, 'r') as f:
            for idx, line in enumerate(f):
                word = line.strip()
                if word[:3] == '.x-' or word[:3] == '.X-':
                    self.word_position.append(idx)

    def init_doc_vectors(self, file, vectors, senses):
        self.init_word_position(file)

        doc_num = 0
        term_weight = Weight.BASE
        with open(file, 'r') as f:
            curr_doc_vectors = defaultdict(int)

            for idx, line in enumerate(f):
                word = line.strip()
                if not word:
                    continue
                if word[:2] == '.I':
                    vectors.append(curr_doc_vectors.copy())
                    senses.append(int(word[-1]))
                    curr_doc_vectors.clear()
                    doc_num += 1
                elif word[:3] == '.x-' or word[:3] == '.X-':
                    curr_doc_vectors[word[3:]] += term_weight
                elif word not in self.stop_list_hash and re.match(r'[a-zA-Z]', word):
                    distance = idx - self.word_position[doc_num]
                    # adjacent-sep-LR
                    # if distance == -1:
                    #     word = 'L-' + word
                    # if distance == 1:
                    #     word = 'R-' + word
                    sign = 6 - abs(distance)
                    pos_term_weight = 1
                    # if abs(distance) == 1:
                    #     pos_term_weight = 6.0
                    # elif abs(distance) <= 3:
                    #     pos_term_weight = 3.0
                    if sign > 0:
                        pos_term_weight = sign
                    # pos_term_weight = term_weight * (1 / abs(distance))
                    curr_doc_vectors[word] += pos_term_weight

            vectors.append(curr_doc_vectors)

        return doc_num

    def create_centroid_vectors(self, vectors, senses):
        V = [0, defaultdict(int), defaultdict(int)]
        for i in range(1, 3601):
            vec = vectors[i]
            sense = senses[i]
            for term in vec:
                V[sense][term] += vec[term]

        sense1_len = len(V[1])
        for k in V[1]:
            V[1][k] /= sense1_len

        sense2_len = len(V[2])
        for k in V[2]:
            V[2][k] /= sense2_len

        return V[1], V[2]

    def predict(self, vec_profile1, vec_profile2, vectors):
        correctness = 0
        info = (
            'NUM      SIM_1      SIM_2     PREDICT    TRUE    CORRECT\n'
            '====    =======    =======    =======    ====    ======='
        )
        print(info)
        for i in range(3601, 4001):
            sim1 = self.calc_cosine_sim(vec_profile1, vectors[i])
            sim2 = self.calc_cosine_sim(vec_profile2, vectors[i])
            predict_sense = 1 if sim1 > sim2 else 2
            correct = '*' if predict_sense == self.sense_num[i] else ' '
            if correct == '*':
                correctness += 1
            row_info = '{0:<4}    {1:<7.4f}    {2:<7.4f}    {3:<7}    {4:<4}    {5}'.format(i, sim1, sim2, predict_sense, self.sense_num[i], correct)
            print(row_info)
        print('Correctness: {}/{}'.format(correctness, 400))
        print('Rate: {}'.format(correctness / 400))

    def kNN_predict(self, vectors):
        kh = kNNHelper(20)
        res = []
        for i in range(3601, 4001):
            predict_sense = kh.fit_and_predict(i, vectors, self.sense_num)
            res.append(predict_sense)

        correctness = 0
        info = (
            'NUM     PREDICT    TRUE    CORRECT\n'
            '====    =======    ====    ======='
        )
        print(info)
        for i in range(3601, 4001):
            predict_sense = res[i - 3601]
            correct = '*' if predict_sense == self.sense_num[i] else ' '
            if correct == '*':
                correctness += 1
            row_info = '{0:<4}    {1:<7}    {2:<4}    {3}'.format(i, predict_sense, self.sense_num[i], correct)
            print(row_info)
        print('Correctness: {}/{}'.format(correctness, 400))
        print('Rate: {}'.format(correctness / 400))

    def start(self):
        # vec1, vec2 = self.create_centroid_vectors(self.doc_vectors, self.sense_num)
        # self.predict(vec1, vec2, self.doc_vectors)

        # kNN Predict, k = 10
        self.kNN_predict(self.doc_vectors)


    def calc_cosine_sim(self, vec1, vec2):
        vec1_norm = sum(v * v for v in vec1.values())
        vec2_norm = sum(v * v for v in vec2.values())
        if len(vec1) > len(vec2):
            vec1, vec2 = vec2, vec1

        cross_product = sum(vec1.get(term, 0) * vec2.get(term, 0) for term in vec1.keys())
        return cross_product / math.sqrt(vec1_norm * vec2_norm)


if __name__ == '__main__':
    engine = IREngine()
    engine.start()