#
# usage: python format_lcquad_data.py {LC-QuAD json file}
#

import re
import os
import sys
import json

# patterns
count_before = re.compile(r'SELECT( DISTINCT|) COUNT(.*) WHERE \{')


def chunked(iterable, n):
    return [iterable[x:x + n] for x in range(0, len(iterable), n)]


def qdict(string, sparql):
    # normalize sparql
    sparql = count_before.sub(r'SELECT (COUNT \2 AS ?tgm_eval_result) WHERE {',
                              sparql)

    return {
        'question': [{
            'language': 'en',
            'string': string
        }],
        'query': {
            'sparql': sparql
        }
    }


def write_file(wd, fn, qs):
    if not os.path.exists(wd):
        os.mkdir(wd)

    twf = wd + fn

    f = open(twf, 'w')
    f.write(json.dumps({'questions': qs}, sort_keys=True, indent=4))
    f.close()


def format_lcquad(wd, fn):
    def fq(q):
        return q.replace('>', '').replace('<', '')

    nof = 0
    qs = [(fq(q.get('verbalized_question', '')), q.get('sparql_query', ''))
          for q in json.load(open(fn))]

    for sqs in chunked(qs, 500):
        tmp = [qdict(q[0], q[1]) for q in sqs]

        nof += 1
        write_file(wd, 'lcquad-{0:02d}.json'.format(nof), tmp)


def main():
    fn = sys.argv[1]
    data_dir = './data/'

    format_lcquad(data_dir, fn)


if __name__ == '__main__':
    main()
