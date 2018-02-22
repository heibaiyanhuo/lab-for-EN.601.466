'''
The basic idea for this classifier is to directly transform each segment into a vector.
There are many features we want to keep when we transform the segment into a vector like term frequencies, whitespaces ratio, non-English words ratio, etc.
Therefore, here I select a special vectorizer TfidVectorizer provided by scikit, which can help us keep these features when transformation.
Then, we use SVM to train our classifier.
'''

import sys
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier

CS466 = '../../'

ORIGINAL_DATA = list()
ORIGINAL_LABELS = list()

COMPRESS_DATA = list()
COMPRESS_LABELS = list()

VECTORIZER = TfidfVectorizer(min_df=1, analyzer='char', lowercase=False)

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
                    COMPRESS_LABELS.append('PTEXT' if ORIGINAL_LABELS[line_ptr] == 'ITEM' else ORIGINAL_LABELS[line_ptr])
                line_ptr = idx
            elif ORIGINAL_LABELS[line_ptr] == '#BLANK#':
                line_ptr = idx

def training():
    features = VECTORIZER.fit_transform(COMPRESS_DATA)
    clf = SGDClassifier(loss='hinge', penalty='l2', alpha=1e-3, random_state=42, max_iter=5, tol=None).fit(features, COMPRESS_LABELS)
    return clf, features


def test(file, clf):
    raw_data = []
    raw_labels = []
    correct = 0
    total = 0
    with open(CS466 + file) as f:
        segment_begin_idx = 0
        segment = ''
        for segment_end_idx, line in enumerate(f):
            label_match = re.match(r'^\S+', line)
            raw_data.append(line)
            raw_labels.append(label_match.group())
            if raw_labels[-1] == '#BLANK#':
                if segment_begin_idx != segment_end_idx:
                    features = VECTORIZER.transform([segment])
                    segment = ''
                    predicted = clf.predict(features)
                    for i in range(segment_begin_idx, segment_end_idx):
                        if predicted[0] == raw_labels[i] or (predicted == 'PTEXT' and (raw_labels[i] == 'ADDRESS' or raw_labels[i] == 'ITEM')):
                            print('.. {}\t{}'.format(predicted[0], raw_data[i]))
                            correct += 1
                        else:
                            print('XX {}\t{}'.format(predicted[0], raw_data[i]))
                        total += 1
                    segment_begin_idx = segment_end_idx + 1
                else:
                    segment_begin_idx += 1
            else:
                segment += line[label_match.span()[1]:]
                if raw_labels[segment_begin_idx] == '#BLANK#':
                    segment_begin_idx = segment_end_idx
    print('Correctness: {}/{}, {}'.format(correct, total, correct/total))

initialize()
clf, features = training()

test(sys.argv[1], clf)