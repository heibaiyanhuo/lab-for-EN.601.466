
class Weight:
    BASE = 1

class DataFile:

    def __init__(self, resource_dir, stemmed=True):
        suffix = '.stemmed' if stemmed else '.tokenized'

        self.tank_docs = resource_dir + '/tank' + suffix
        self.plant_docs = resource_dir + '/plant' + suffix
        self.perplace_docs = resource_dir + '/perplace' + suffix

        self.common_words = resource_dir + '/common_words'

        if stemmed:
            self.common_words += suffix