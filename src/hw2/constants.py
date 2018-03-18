
class Weight:
    TITLE = 3  # weight given a title token
    KEYWD = 4  # weight given a key word token
    AUTHR = 3  # weight given an an author token
    ABSTR = 1  # weight given an abstract word token
    QUERY_BASE = 2
    QUERY_AUTH = 2


class DataFile:

    def __init__(self, DIR, HOME, stemmed=True):
        suffix = '.stemmed' if stemmed else '.tokenized'
        self.token_docs = DIR + "/cacm" + suffix
        self.corps_freq = DIR + "/cacm" + suffix + '.hist'
        self.stoplist = DIR + '/common_words'
        self.titles = DIR + '/titles.short'
        self.token_qrys = DIR + '/query' + suffix
        self.query_freq = DIR + '/query' + suffix + '.hist'
        self.query_relv = DIR + "/query.rels"

        self.token_intr = HOME + '/interactive' + suffix
        self.inter_freq = HOME + '/interactive' + suffix + '.hist'
        if stemmed:
            self.stoplist += '.stemmed'
