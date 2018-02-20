import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier

CS466 = '../../'

ORIGINAL_DATA = list()
ORIGINAL_LABELS = list()

COMPRESS_DATA = list()
COMPRESS_LABELS = list()



def initialize():
    with open(CS466 + 'segment/segment.data.train') as f:
        line_ptr = 0
        for idx, line in enumerate(f):
            label_match = re.match(r'^\S+', line)
            ORIGINAL_DATA.append(line[label_match.span()[1]:].strip())
            ORIGINAL_LABELS.append(label_match.group())
            if ORIGINAL_LABELS[-1] == '#BLANK#':
                if ORIGINAL_LABELS[line_ptr] != '#BLANK#':
                    info = ''
                    for l in ORIGINAL_DATA[line_ptr:idx]:
                        info += l
                    COMPRESS_DATA.append(info)
                    COMPRESS_LABELS.append(ORIGINAL_LABELS[line_ptr])
                line_ptr = idx
            elif ORIGINAL_LABELS[line_ptr] == '#BLANK#':
                line_ptr = idx

def training():
    vectorizer = TfidfVectorizer(min_df=1, analyzer='char', lowercase=False)
    features = vectorizer.fit_transform(COMPRESS_DATA)
    clf = SGDClassifier(loss='hinge', penalty='l2', alpha=1e-3, random_state=42, max_iter=5, tol=None).fit(features[:800], COMPRESS_LABELS[:800])
    return clf, features

initialize()
clf, features = training()
# print(len(ORIGINAL_DATA))
# print(len(COMPRESS_DATA))
# print(len(COMPRESS_LABELS))
# print(COMPRESS_DATA[:3])
# print(COMPRESS_LABELS[:3])
predicted = clf.predict(features[800:])
print(np.mean(predicted == COMPRESS_LABELS[800:]))
# print(predicted)