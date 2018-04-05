import math
import bisect

class kNNHelper:

    def __init__(self, K):
        self.nearest_vectors = []
        self.K = K

    def fit_and_predict(self, index, vectors, senses):
        self.nearest_vectors.clear()
        print('Fit model for vector {}.'.format(index))
        for i in range(1, 3601):
            d = self.calc_distance(vectors[index], vectors[i])
            bisect.insort(self.nearest_vectors, (d, i))
            if len(self.nearest_vectors) > self.K:
                self.nearest_vectors.pop()

        print('Predicting...')
        count = [0, 0, 0]
        for d, i in self.nearest_vectors:
            sense = senses[i]
            count[sense] += 1

        return 1 if count[1] > count[2] else 2

    def calc_distance(self, vec1, vec2):
        distance = 0

        for k in vec1:
            v1 = vec1[k]
            v2 = vec2.get(k, 0)
            distance += (v1 - v2) ** 2

        for k in vec2:
            if not k in vec1:
                distance += vec2[k] ** 2

        return math.sqrt(distance)