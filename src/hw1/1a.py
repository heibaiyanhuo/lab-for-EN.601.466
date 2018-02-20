import sys
import re

CS466 = '../../'

ABBREVS = set()
SI = set()
TITLES = set()
UPN = set()
TIME = set()

CORRECT = 0
TOTAL = 0

RULE_CORRECT = [0] * 10
RULE_TOTAL = [0] * 10

def initialize():
    global CS466, ABBREVS, TITLES, UPN, SI, TIME
    with open(CS466 + 'classes/abbrevs') as f:
        for line in f:
            ABBREVS.add(line.strip())
    with open(CS466 + 'classes/titles') as f:
        for line in f:
            TITLES.add(line.strip())
    with open(CS466 + 'classes/unlikely_proper_nouns') as f:
        for line in f:
            UPN.add(line.strip())
    with open(CS466 + 'classes/sentence_internal') as f:
        for line in f:
            SI.add(line.strip())
    with open(CS466 + 'classes/timeterms') as f:
        for line in f:
            TIME.add(line.strip())

def classifier(file):
    global CS466, ABBREVS, TITLES, UPN, SI, TIME
    with open(CS466 + file) as f:
        for line in f:
            line_arr = line.strip().split()
            if re.match(r'^<P>$', line_arr[6]):
                ret(line_arr[1], 'EOS', line_arr[0], '1')
            elif re.match(r'^([a-z]|[,.!?;:])', line_arr[6]):
                ret(line_arr[1], 'NEOS', line_arr[0], '2')
            elif re.match(r'^[A-Z]', line_arr[6]) and line_arr[6].lower() in UPN:
                ret(line_arr[1], 'EOS', line_arr[0], '3')
            elif re.match(r'^[A-Z]$', line_arr[4]):
                ret(line_arr[1], 'NEOS', line_arr[0], '4')
            elif line_arr[4] in SI or line_arr[4] in TIME:
                ret(line_arr[1], 'NEOS', line_arr[0], '5')
            elif re.match(r'^([A-Z|a-z]\.)*[A-Z|a-z]$', line_arr[4]):
                ret(line_arr[1], 'NEOS', line_arr[0], '6')
            elif re.match(r'^[A-Z|0-9|-]', line_arr[6]):
                if line_arr[4].lower() == 'no' and re.match(r'^[^0-9]', line_arr[6]):
                    ret(line_arr[1], 'EOS', line_arr[0], '7')
                elif line_arr[4].lower() in TITLES:
                    ret(line_arr[1], 'NEOS', line_arr[0], '8')
                elif line_arr[4].lower() in ABBREVS:
                    ret(line_arr[1], 'NEOS', line_arr[0], '9')
                else:
                    ret(line_arr[1], 'EOS', line_arr[0], '10', line)
            else:
                ret(line_arr[1], 'EOS', line_arr[0], '10', line)


def ret(id, given_class, true_class, rule, line=''):
    global CORRECT, TOTAL, RULE_CORRECT, RULE_TOTAL
    if given_class == true_class:
        CORRECT += 1
        RULE_CORRECT[int(rule) - 1] += 1
    else:
        # pass
        # print(line)
        print('Error in {}, given class is {}, true class is {}, rule {}'.format(id, given_class, true_class, rule))
    TOTAL += 1
    RULE_TOTAL[int(rule) - 1] += 1



initialize()
classifier(sys.argv[1])

print('Correctness: {}/{}, {}'.format(CORRECT, TOTAL, CORRECT/TOTAL))
print(RULE_CORRECT)
print(RULE_TOTAL)
print([0 if RULE_TOTAL[i] == 0 else RULE_CORRECT[i] / RULE_TOTAL[i] for i in range(0, 9)])

