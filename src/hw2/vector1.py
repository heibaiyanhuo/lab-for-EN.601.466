import sys
import re
import subprocess
import math
from collections import defaultdict

from constants import Weight, DataFile
from SVDExtension import SVDExtension

# DIR, file_name = os.path.split(os.path.realpath(__file__))

DIR = './assets/'
HOME = "."

class IREngine:

    def __init__(self):
        # doc_vector:
        # An array of hashes, each array index indicating a particular
        # query's weight "vector". (See more detailed below)
        self.doc_vectors = []

        # qry_vector:
        # An array of hashes, each array index indicating a particular query's
        # weight "vector".
        self.qry_vectors = []

        # docs_freq_hash
        #
        # dictionary which holds <token, frequency> pairs where
        # docs_freq_hash[token] -> frequency
        #   token     = a particular word or tag found in the cacm corpus
        #   frequency = the total number of times the token appears in
        #               the corpus.
        self.docs_freq_hash = defaultdict(int)

        # corp_freq_hash
        #
        # dictionary which holds <token, frequency> pairs where
        # corp_freq_hash[token] -> frequency
        #   token     = a particular word or tag found in the corpus
        #   frequency = the total number of times the token appears per
        #               document-- that is a token is counted only once
        #               per document if it is present (even if it appears
        #               several times within that document).
        self.corp_freq_hash = defaultdict(int)

        # stoplist_hash
        #
        # common list of uninteresting words which are likely irrelvant
        # to any query.
        # for given "word" you can do:   `if word in stoplist_hash` to check
        # if word is in stop list
        #
        #   Note: this is an associative array to provide fast lookups
        #         of these boring words
        self.stoplist_hash = set()

        # titles_vector
        #
        # vector of the cacm journal titles. Indexed in order of apperance
        # within the corpus.
        self.title_vectors = []

        # relevance_hash
        #
        # a hash of hashes where each <key, value> pair consists of
        #
        #   key   = a query number
        #   value = a hash consisting of document number keys with associated
        #           numeric values indicating the degree of relevance the
        #           document has to the particular query.
        #   relevance_hash[query_num][doc_num] = 1, if given query and doc is relavent
        self.relevance_hash = defaultdict(lambda: defaultdict(int))

        # doc_simula
        #
        # array used for storing query to document or document to document
        # similarity calculations (determined by cosine_similarity, etc. )
        self.doc_simula_list = []

        # res_vector
        #
        # array used for storing the document numbers of the most relevant
        # documents in a query to document or document to document calculation.
        self.res_vector_idx_list = []

        self.total_docs = 0
        self.total_qrys = 0

        self.doc_idf_list = []
        self.d_f_hash = defaultdict(int)
        self.qry_idf_list = []
        self.q_f_hash = defaultdict(int)


        print('INITIALIZING VECTORS ... ')
        self.datafile = DataFile(DIR, HOME)
        self.init_corp_freq()
        self.init_doc_vectors()
        self.init_qry_vectors()

        self.set_TFIDF_weight()

        # self.SVDExtension = SVDExtension(self.corp_freq_hash)
        # self.SVDExtension.init_svd_mat(self.doc_vectors, self.qry_vectors)

    '''
    INIT_CORP_FREQ
    
    This function reads in corpus and document frequencies from
    the provided histogram file for both the document set
    and the query set. This information will be used in
    term weighting.

    It also initializes the arrays representing the stoplist,
    title list and relevance of document given query.
    '''
    def init_corp_freq(self):
        with open(self.datafile.corps_freq, 'r') as f:
            for line in f:
                data_per_line = line.strip().split()
                if len(data_per_line) == 3:
                    doc_freq, corp_freq, term = data_per_line
                    self.docs_freq_hash[term] = int(doc_freq)
                    self.d_f_hash[term] = int(doc_freq)
                    self.corp_freq_hash[term] = int(corp_freq)

        with open(self.datafile.query_freq, 'r') as f:
            for line in f:
                data_per_line = line.strip().split()
                if len(data_per_line) == 3:
                    doc_freq, corp_freq, term = data_per_line
                    self.docs_freq_hash[term] += int(doc_freq)
                    self.q_f_hash[term] = int(doc_freq)
                    self.corp_freq_hash[term] += int(corp_freq)

        with open(self.datafile.stoplist, 'r') as f:
            for line in f:
                if line:
                    self.stoplist_hash.add(line.strip())

        self.title_vectors.append('')
        with open(self.datafile.titles, 'r') as f:
            for line in f:
                if line:
                    self.title_vectors.append(line.strip())

        with open(self.datafile.query_relv, 'r') as f:
            for line in f:
                if line:
                    qry_num, rel_doc = map(int, line.strip().split())
                    self.relevance_hash[qry_num][rel_doc] = 1

    '''
    INIT_DOC_VECTORS

    This function reads in tokens from the document file.
    When a .I token is encountered, indicating a document
    break, a new vector is begun. When individual terms
    are encountered, they are added to a running sum of
    term frequencies. To save time and space, it is possible
    to normalize these term frequencies by inverse document
    frequency (or whatever other weighting strategy is
    being used) while the terms are being summed or in
    a posthoc pass.  The 2D vector array

      doc_vector[ doc_num ][ term ]
    
    stores these normalized term weights.

    It is possible to weight different regions of the document
    differently depending on likely importance to the classification.
    The relative base weighting factors can be set when
    different segment boundaries are encountered.

    This function is currently set up for simple TF weighting.
    '''
    def init_doc_vectors(self):
        doc_num = 0
        BASE_WEIGHT = {
            '.T': Weight.TITLE,
            '.K': Weight.KEYWD,
            '.W': Weight.ABSTR,
            '.A': Weight.AUTHR
        }
        term_weight = 0

        with open(self.datafile.token_docs, 'r') as f:
            curr_doc_vector = defaultdict(int)
            for line in f:
                word = line.strip()
                if not word or word == '.I 0':
                    continue # Skip empty line
                if word[:2] == '.I':
                    self.doc_vectors.append(curr_doc_vector.copy())
                    curr_doc_vector.clear()
                    doc_num += 1
                elif word in BASE_WEIGHT:
                    term_weight = BASE_WEIGHT[word]
                elif word not in self.stoplist_hash and re.match(r'[a-zA-Z]', word):
                    if self.docs_freq_hash[word] == 0:
                        print('Error: Document frequency of zero: {}\n'.format(word))
                        exit()
                    curr_doc_vector[word] += term_weight
                    # curr_doc_vector[word] = 1
            self.doc_vectors.append(curr_doc_vector)
        self.total_docs = doc_num

    '''
    INIT_QRY_VECTORS

    This function should be nearly identical to the step
    for initializing document vectors.

    This function is currently set up for simple TF weighting.
    '''
    def init_qry_vectors(self):
        qry_num = 0
        QUERY_WEIGHT = {
            '.W': Weight.QUERY_BASE,
            '.A': Weight.QUERY_AUTH
        }
        term_weight = 0
        with open(self.datafile.token_qrys, 'r') as f:
            curr_qry_vector = defaultdict(int)
            for line in f:
                word = line.strip()
                if not word or word == '.I 0':
                    continue
                if word[:2] == '.I':
                    self.qry_vectors.append(curr_qry_vector.copy())
                    curr_qry_vector.clear()
                    qry_num += 1
                elif word in QUERY_WEIGHT:
                    term_weight = QUERY_WEIGHT[word]
                elif word not in self.stoplist_hash and re.match(r'[a-zA-Z]', word):
                    if self.docs_freq_hash[word] == 0:
                        print('Error: Document frequency of zero: {}\n'.format(word))
                        exit()
                    curr_qry_vector[word] += term_weight
                    # curr_qry_vector[word] = 1
            self.qry_vectors.append(curr_qry_vector)
        self.total_qrys = qry_num


    def set_TFIDF_weight(self):
        for vector in self.doc_vectors:
            for key in vector:
                vector[key] *= math.log(self.total_docs / self.d_f_hash[key], 10)

        for vector in self.qry_vectors:
            for key in vector:
                vector[key] *= math.log(self.total_qrys / self.q_f_hash[key], 10)

    '''
    MAIN_LOOP
    
    Parameters: currently no explicit parameters.
                performance dictated by user input.
    
    Initializes document and query vectors using the
    input files specified in &init_files. Then offers
    a menu and switch to appropriate functions in an
    endless loop.
    
    Possible extensions at this level:  prompt the user
    to specify additional system parameters, such as the
    similarity function to be used.
    
    Currently, the key parameters to the system (stemmed/unstemmed,
    stoplist/no-stoplist, term weighting functions, vector
    similarity functions) are hardwired in.
    
    Initializing the document vectors is clearly the
    most time consuming section of the program, as 213334
    to 258429 tokens must be processed, weighted and added
    to dynamically growing vectors.
    
    '''
    def start_loop(self):
        menu = (
            '============================================================\n'
            '==      Welcome to the 600.466 Vector-based IR Engine       \n'
            '==                                                          \n'
            '==      Total Documents: {0}                                \n'
            '==      Total Queries: {1}                                  \n'
            '============================================================\n'
            '                                                            \n'
            'OPTIONS:                                                    \n'
            '  1 = Find documents most similar to a given query or document\n'
            '  2 = Compute precision/recall for the full query set         \n'
            '  3 = Compute cosine similarity between two queries/documents \n'
            '  4 = Quit                                                    \n'
            '                                                              \n'
            '============================================================\n'
        ).format(self.total_docs, self.total_qrys)

        while True:
            print(menu)
            option = input('Enter Option: ')
            if option == '1':
                self.set_and_show_retrieved_set()
            elif option == '2':
                self.full_precision_recall_test()
            elif option == '3':
                self.do_full_cosine_similarity()
            elif option == '4':
                exit()
            else:
                print('Input seems not right, try again\n')

    '''
    GET_AND_SHOW_RETRIEVED_SET

    This function requests key retrieval parameters,
    including:

    A) Is a query vector or document vector being used
       as the retrieval seed? Both are vector representations
       but they are stored in different data structures,
       and one may optionally want to treat them slightly
       differently.

    B) Enter the number of the query or document vector to
       be used as the retrieval seed.
    
       Alternately, one may wish to request a new query
       from standard input here (and call the appropriate
       tokenization, stemming and term-weighting routines).
    
    C) Request the maximum number of retrieved documents
       to display.
    '''
    def set_and_show_retrieved_set(self):
        menu = (
            'Find documents similar to:  \n'
            '(1) a query from "query.raw"\n'
            '(2) an interactive query    \n'
            '(3) another document        \n'
        )
        print(menu)
        command_type = input("Choice: ").strip()
        vector_num = None
        if not re.match(r'[123]$', command_type):
            print('The input is not valid. By default use option 1')
            command_type = '1'

        if command_type != '2':
            vector_num = int(input('Target Document/Query number: ').strip())

        max_show = int(input('Show how many matching documents (e.g. 20): ').strip())

        if command_type == '3':
            print('Document to Document comparison')
            self.set_retrieved_set(self.doc_vectors[vector_num])
            self.shw_retrieved_set(max_show, vector_num, self.doc_vectors[vector_num], 'Document')
        elif command_type == '2':
            print('Interactive Query to Document comparison')
            interact_vector = self.gen_interact_vec()
            self.set_retrieved_set(interact_vector)
            self.shw_retrieved_set(max_show, 0, interact_vector, 'Interactive Query')
        else:
            print('Query to Document comparison')
            self.set_retrieved_set(self.qry_vectors[vector_num], vector_num)
            self.shw_retrieved_set(max_show, vector_num, self.qry_vectors[vector_num], 'Query')
            rp_result = self.comp_recall(self.relevance_hash[vector_num])
            self.show_relevance(vector_num, rp_result)

    '''
    SET_RETRIEVED_SET
    
    Parameters:
    
    my_qry_vector    - the query vector to be compared with the
                  document set. May also be another document
                  vector.

    This function computes the document similarity between the
    given vector "my_qry_vector" and all vectors in the document
    collection storing these values in the array "doc_simula"

    An array of the document numbers is then sorted by this
    similarity function, forming the rank order of documents
    for use in the retrieval set.

    The similarity will be sorted in descending order.
    '''
    def set_retrieved_set(self, my_doc_vector, doc_num=None):
        self.doc_simula_list.clear()
        self.res_vector_idx_list = None

        total_number = len(self.doc_vectors) - 1
        self.doc_simula_list.append(0)

        for i in range(1, total_number + 1):
            self.doc_simula_list.append(self.calc_cosine_sim_a(my_doc_vector, self.doc_vectors[i]))
            # self.doc_simula_list.append(self.SVDExtension.calc_cosine_sim(doc_num, i, True))

        self.res_vector_idx_list = sorted(range(1, total_number + 1), key=lambda x: -self.doc_simula_list[x])

    '''
    SHW_RETRIEVED_SET
    
    Assumes the following global data structures have been
    initialized, based on the results of "set_retrieved_set".

    1) res_vector - contains the document numbers sorted in
                    rank order
    2) doc_simula - The similarity measure for each document,
                    computed by set_retrieved_set.
    
    Also assumes that the following have been initialized in
    advance:

       titles[ doc_num ]    - the document title for a
                                document number, $doc_num
       relevance_hash[ qry_num ][ doc_num ]
                            - is doc_num relevant given
                                query number, qry_num

    Parameters:
        max_show   - the maximum number of matched documents
                to display.
        qry_num    - the vector number of the query
        qry_vect   - the query vector (passed by reference)
        comparison - "Query" or "Document" (type of vector
                being compared to)

    In the case of "Query"-based retrieval, the relevance
    judgements for the returned set are displayed. This is
    ignored when doing document-to-document comparisons, as
    there are nor relevance judgements.
    '''
    def shw_retrieved_set(self, max_show, qry_num, my_doc_vector, comparison):
        menu = (
            '   ************************************************************\n'
            '         Documents Most Similar To {0} number {1}       \n'
            '   ************************************************************\n'
            '   Similarity   Doc#  Author      Title                        \n'
            '   ==========   ===  ========     =============================\n'
            ).format(comparison, qry_num)

        print(menu)

        for i in range(max_show + 1):
            idx = self.res_vector_idx_list[i]
            if comparison == 'Query' and self.relevance_hash[qry_num][idx]:
                sys.stdout.write('* ')
            else:
                sys.stdout.write('  ')

            similarity = self.doc_simula_list[idx]
            title = self.title_vectors[idx][:47]

            print(' {0:10.8f}   {1}'.format(similarity, title))

        show_terms = input('\nShow the terms that overlap between the query and retrieved docs (y/n): ').strip()
        if show_terms != 'n' and show_terms != 'N':
            for i in range(max_show + 1):
                idx = self.res_vector_idx_list[i]
                self.show_overlap(my_doc_vector, self.doc_vectors[idx], qry_num, idx)
                if i % 5 == 4:
                    cont = input('\nContinue (y/n)?: ').strip()
                    if cont == 'n' or cont == 'N':
                        break

    def gen_interact_vec(self):
        subprocess.call(DIR + '/interactive.prl')
        interact_vector = []
        qry_num = 0
        QUERY_WEIGHT = {
            '.W': Weight.QUERY_BASE,
            '.A': Weight.QUERY_AUTH
        }
        term_weight = 0
        with open(self.datafile.token_intr, 'r') as f:
            curr_qry_vector = defaultdict(int)
            for line in f:
                word = line.strip()
                if not word or word == '.I 0':
                    continue
                if word[:2] == '.I':
                    interact_vector.append(curr_qry_vector.copy())
                    curr_qry_vector.clear()
                    qry_num += 1
                elif word in QUERY_WEIGHT:
                    term_weight = QUERY_WEIGHT[word]
                elif word not in self.stoplist_hash and re.match(r'[a-zA-Z]', word):
                    if self.docs_freq_hash[word] == 0:
                        print('Error: Document frequency of zero: {}\n'.format(word))
                        exit()
                    curr_qry_vector[word] += term_weight
        return interact_vector[0]

    '''
    COMPUTE_PREC_RECALL

	Like "shw_retrieved_set", this function makes use of the following
	data structures which may either be passed as parameters or
	used as global variables. These values are set by the function
	&get_retrieved_set.

	1) doc_simila[ rank ] - contains the document numbers sorted
	                         in rank order based on the results of
	                         the similarity function

	2) res_vector[ docn ] - The similarity measure for each document,
	                         relative to the query vector ( computed by
	                         "set_retrieved_set").

	Also assumes that the following have been initialzied in advance:
	      titles[ docn ]       - the document title for a document
	                               number $docn
	      relevance_hash[ qvn ][ docn ]
	                             - is $docn relevant given query number
	                               $qvn

	The first step of this function should be to take the rank ordering
	of the documents given a similarity measure to a query
	(i.e. the list docs_sorted_by_similarity[rank]) and make a list
	of the ranks of just the relevant documents. In an ideal world,
	if there are k=8 relevant documents for a query, for example, the list
	of rank orders should be (1 2 3 4 5 6 7 8) - i.e. the relevant documents
	are the top 8 entries of all documents sorted by similarity.
	However, in real life the relevant documents may be ordered
	much lower in the similarity list, with rank orders of
	the 8 relevant of, for example, (3 27 51 133 159 220 290 1821).

	Given this list, compute the k (e.g. 8) recall/precison pairs for
	the list (as discussed in class). Then to determine precision
	at fixed levels of recall, either identify the closest recall
	level represented in the list and use that precision, or
	do linear interpolation between the closest values.

	This function should also either return the various measures
	of precision/recall specified in the assignment, or store
	these values in a cumulative sum for later averaging.
    '''
    def comp_recall(self, relevance_qry_hash):
        rank = [0]

        for index, item in enumerate(self.res_vector_idx_list):
            if relevance_qry_hash[item] == 1:
                rank.append(index + 1)
        TOTAL_RELEVANT = len(rank) - 1
        res = []
        for i in range(1, TOTAL_RELEVANT + 1):
            recall = i/TOTAL_RELEVANT
            precision = i/rank[i]
            doc_num = self.res_vector_idx_list[rank[i] - 1]
            res.append([i, rank[i], recall, precision, doc_num])
        return res

    '''
    SHOW_RELVNT

    This function should take the rank orders and similarity
    arrays described in &show_retrieved_set and &comp_recall
    and print out only the relevant documents, in an order
    and manner of presentation very similar to &show_retrieved_set.
    '''
    def show_relevance(self, vector_num, rp_result):
        info = (
            '   *****************************************************\n'
            '        Documents Most relevant To Query number {0}       \n'
            '   *****************************************************\n'
            '   NUM    RANK      REC        PREC        DOC#           \n'
            '   ===    ====    =======    ========      ===='
        ).format(vector_num)
        print(info)
        for one_rank in rp_result:
            sys.stdout.write('   {0:<3}    {1:<4}    {2:<7.4f}    {3:<8.4f}      {4:<4}\n'.format(one_rank[0], one_rank[1], one_rank[2], one_rank[3], one_rank[4]))

    '''
    SHOW_OVERLAP

    Parameters:
        - Two vectors (qry_vect and doc_vect), passed by
        reference.
        - The number of the vectors for display purposes
    
    PARTIALLY IMPLEMENTED:

    This function should show the terms that two vectors
    have in common, the relative weights of these terms
    in the two vectors, and any additional useful information
    such as the document frequency of the terms, etc.

    Useful for understanding the reason why documents
    are judged as relevant.

    Present in a sorted order most informative to the user.
    '''
    def show_overlap(self, my_qry_vector, my_doc_vector, qry_num, doc_num):
        info = (
           '============================================================\n'
           '{0:15s}  {1:8d}   {2:8d}\t{3}\n'
           '============================================================'
        ).format('Vector Overlap', qry_num, doc_num, 'Docfreq')
        print(info)
        for term_one, weight_one in my_qry_vector.items():
            if my_doc_vector.get(term_one):
                info = '{0:15s}  {1}   {2}\t{3}\n'.format(term_one, weight_one, my_doc_vector[term_one], self.docs_freq_hash[term_one])
                print(info)

    def full_precision_recall_test(self):
        P_1 = [0]
        P_2 = [0]
        P_3 = [0]
        P_4 = [0]
        P_mean_1= [0]
        P_mean_2 = [0]
        P_norm = [0]
        R_norm = [0]
        for i in range(1, self.total_qrys + 1):
            print('Calculating for query {}...'.format(i))
            print('---------------------------')
            self.set_retrieved_set(self.qry_vectors[i])
            rp_result = self.comp_recall(self.relevance_hash[i])
            has_p1 = False
            has_p2 = False
            total_rel = len(rp_result)
            if total_rel == 0:
                print('No relevant docs!')
                continue
            rank = [one[1] for one in rp_result]
            N = self.total_docs
            R_norm.append(1 - (sum(rank) - sum(range(1, total_rel + 1))) / ((N - total_rel) * total_rel))

            tmp0 = sum([math.log(x) for x in rank]) - sum([math.log(i) for i in range(1, total_rel + 1)])
            tmp1 = N * math.log(N) - (N - total_rel) * math.log(N - total_rel) - total_rel * math.log(total_rel)
            P_norm.append(1 - tmp0 / tmp1)

            P_4.append(rp_result[-1][3])
            if total_rel < 4:
                print('No enough relevant docs to calculate precision mean 1, skip')
            else:
                has_p1 = True
                P_1.append(rp_result[round(total_rel / 4) - 1][3])
                P_2.append(rp_result[round(total_rel / 2) - 1][3])
                P_3.append(rp_result[round(3 * total_rel / 4) - 1][3])

                P_mean_1.append((P_1[-1] + P_2[-1] + P_3[-1]) / 3)

            if total_rel < 10:
                print('No enough relevant docs to calculate precision mean 2, skip.')
            else:
                has_p2 = True
                s = sum([rp_result[round(i * total_rel / 10) - 1][3] for i in range(1, 11)])
                P_mean_2.append(s / 10)

            print('For Query {}'.format(i))
            print('P_0.25: {}'.format(P_1[-1] if has_p1 else 'N/A'))
            print('P_0.5: {}'.format(P_2[-1] if has_p1 else 'N/A'))
            print('P_0.75: {}'.format(P_3[-1] if has_p1 else 'N/A'))
            print('P_1: {}'.format(P_4[-1]))
            print('P_mean1: {}'.format(P_mean_1[-1] if has_p1 else 'N/A'))
            print('P_mean2: {}'.format(P_mean_2[-1] if has_p2 else 'N/A'))
            print('P_norm: {}'.format(P_norm[-1]))
            print('R_norm: {}'.format(R_norm[-1]))
            print('==========================\n')

        print('For {} queries on average: '.format(self.total_qrys))
        print('---------------------------')
        print('P_0.25: {}'.format(sum(P_1) / (len(P_1) - 1) if len(P_1) > 1 else 'N/A'))
        print('P_0.5: {}'.format(sum(P_2) / (len(P_2) - 1) if len(P_2) > 1 else 'N/A'))
        print('P_0.75: {}'.format(sum(P_3) / (len(P_3) - 1) if len(P_3) > 1 else 'N/A'))
        print('P_1: {}'.format(sum(P_4) / (len(P_4) - 1)) if len(P_4) > 1 else 'N/A')
        print('P_mean_1: {}'.format(sum(P_mean_1) / (len(P_mean_1) - 1) if len(P_mean_1) > 1 else 'N/A'))
        print('P_mean_2: {}'.format(sum(P_mean_2) / (len(P_mean_2) - 1) if len(P_mean_2) > 1 else 'N/A'))
        print('P_norm: {}'.format(sum(P_norm) / (len(P_norm) - 1) if len(P_norm) > 1 else 'N/A'))
        print('R_norm: {}'.format(sum(R_norm) / (len(R_norm) - 1) if len(R_norm) > 1 else 'N/A'))
        print('==========================\n')


    def full_cosine_similarity(self, my_qry_vector, my_doc_vector, qry_num, doc_num):
        sim = self.calc_cosine_sim_a(my_qry_vector, my_doc_vector)
        print('Similarity between Query {} and Doc {} is {}'.format(qry_num, doc_num, sim))

    def do_full_cosine_similarity(self):
        qry_num = int(input('\n1st is Query number: ').strip())
        doc_num = int(input('\n2nd is Document number: ').strip())
        self.full_cosine_similarity(self.qry_vectors[qry_num], self.doc_vectors[doc_num], qry_num, doc_num)

    def calc_cosine_sim_a(self, vec1, vec2, vec1_norm=0.0, vec2_norm=0.0):
        if not vec1_norm:
            vec1_norm = sum(v * v for v in vec1.values())
        if not vec2_norm:
            vec2_norm = sum(v * v for v in vec2.values())

        # save some time of iterating over the shorter vec
        if len(vec1) > len(vec2):
            vec1, vec2 = vec2, vec1

        # calculate the cross product
        cross_product = sum(vec1.get(term, 0) * vec2.get(term, 0) for term in vec1.keys())
        return cross_product / math.sqrt(vec1_norm * vec2_norm)

    def calc_dice_sim(self, vec1, vec2, vec1_norm=0.0, vec2_norm=0.0):
        if not vec1_norm:
            vec1_norm = sum(v for v in vec1.values())
        if not vec2_norm:
            vec2_norm = sum(v for v in vec2.values())
        if len(vec1) > len(vec2):
            vec1, vec2 = vec2, vec1

        cross_product = sum(vec1.get(term, 0) * vec2.get(term, 0) for term in vec1.keys())
        return 2 * cross_product / (vec1_norm + vec2_norm)

    def calc_cosine_sim_b(self, vec1, vec2, vec1_norm=0.0, vec2_norm=0.0):
        return self.calc_cosine_sim_a(vec1, vec2, vec1_norm, vec2_norm)


if __name__ == "__main__":
    engine = IREngine()
    engine.start_loop()






