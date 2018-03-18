import math
import numpy as np

class SVDExtension:

    def __init__(self, corp_hash):
        self.all_terms = dict()
        i = 0
        for k in corp_hash:
            self.all_terms[k] = i
            i += 1
        self.u_d = None
        self.sigma_d = None
        self.vh_d = None
        self.k_d = None # Reduce dim
        self.doc_weight_mat = None

        self.u_q = None
        self.sigma_q = None
        self.vh_q = None
        self.k_q = None
        self.qry_weight_mat = None

    def init_svd_mat(self, doc_vectors, qry_vectors):
        term_num = len(self.all_terms)
        # init doc svd mat
        doc_num = len(doc_vectors) - 1
        doc_original_mat = np.zeros([doc_num, term_num])
        for i in range(1, doc_num + 1):
            for k, v in doc_vectors[i].items():
                doc_original_mat[i - 1][self.all_terms[k]] = v
        print('Initialize doc svd mat...')
        self.u_d, self.sigma_d, self.vh_d = np.linalg.svd(doc_original_mat)
        print('Reduce dim')
        origin_sum_square = np.square(self.sigma_d).sum()
        new_sum_square = 0.0
        for i in range(len(self.sigma_d)):
            new_sum_square += self.sigma_d[i]**2
            if new_sum_square / origin_sum_square >= 0.9:
                self.k_d = i
                break
        print('New dim is {}'.format(self.k_d))
        self.doc_weight_mat = np.dot(self.u_d[:, :self.k_d] * self.sigma_d[:self.k_d], self.vh_d[:self.k_d, :])

        qry_num = len(qry_vectors) - 1
        qry_original_mat = np.zeros([qry_num, term_num])
        for i in range(1, qry_num + 1):
            for k, v in qry_vectors[i].items():
                qry_original_mat[i - 1][self.all_terms[k]] = v
        print('Initialize qry svd mat')
        self.u_q, self.sigma_q, self.vh_q = np.linalg.svd(qry_original_mat)
        print('Reduce dim')
        origin_sum_square = np.square(self.sigma_q).sum()
        new_sum_square = 0.0
        for index, x in enumerate(self.sigma_q):
            new_sum_square += x*x
            if new_sum_square / origin_sum_square >= 0.9:
                self.k_q = index
                break
        print('New dim is {}'.format(self.k_q))
        self.qry_weight_mat = np.dot(self.u_q[:, :self.k_q] * self.sigma_q[:self.k_q], self.vh_q[:self.k_q, :])

    def calc_cosine_sim(self, doc_num1, doc_num2, query=True):
        vec1 = None
        if query:
            vec1 = self.qry_weight_mat[doc_num1 - 1, :]
        else:
            vec1 = self.doc_weight_mat[doc_num1 - 1, :]
        vec2 = self.doc_weight_mat[doc_num2 - 1, :]
        n = min(vec1.shape[0], vec2.shape[0])
        return np.dot(vec1[:n], vec2[:n]) / math.sqrt(np.square(vec1[:n]).sum() * np.square(vec2[:n]).sum())