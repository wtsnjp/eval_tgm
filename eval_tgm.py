#
# usage: python eval_tgm.py {json file} ...
#

import os
import sys
import json
import requests

# logging
from logging import getLogger, StreamHandler, Formatter, DEBUG

logger    = getLogger(__name__)
handler   = StreamHandler()
formatter = Formatter('%(levelname)s: %(message)s')

handler.setLevel(DEBUG)
handler.setFormatter(formatter)

logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False

# private functions
def load_qald_dataset(fn, lang):
    """
    Load QALD dataset (json file)

    :param fn: filename
    :param lang: language
    :return: list of 3-tuples (NL question, answertype, SPARQL query)
    """
    qs = []

    for e in json.load(open(fn))['questions']:
        tmp_q, tmp_a, tmp_s = None, None, None

        # NL question
        for q in e['question']:
            if q['language'] == lang:
                tmp_q = q['string']
                break

        # answertype
        tmp_a = e['answertype']

        # SPARQL query
        if 'sparql' in e['query']:
            tmp_s = e['query']['sparql']

        if tmp_q and tmp_a and tmp_s:
            qs.append((tmp_q, tmp_a, tmp_s))

    return qs

def run_tgm(question, lang, tgm_url):
    """
    Run TGM of OKBQA using REST API

    :param question: NL question
    :param lang: language
    :param tgm_url: REST API's endpoint of TGM
    :return: json data including {"query", "score", "slots"}
    """
    tgm_in = '{ "string": "%s", "language": "%s" }' % (question, lang)
    r = requests.post(tgm_url, data=tgm_in)
    return json.loads(r.text)

# public functions
def prepare_data(fns, lang='en',
                 tgm_url='http://ws.okbqa.org:1515/templategeneration/rocknrole'):
    """
    Prepare data for evaluation (use cache if exists)

    :param fn: list of filenames
    :param lang: (optional) language
    :param tgm_url: (optional) REST API's endpoint of TGM
    :return: list of dicts (whole data)
    """
    data = []

    for fn in fns:
        # cache file name
        bn, ext = os.path.splitext(os.path.basename(fn))
        if ext != '.json':
            logger.warning('Input file "{}{}" is not a json file; skipping'.format(bn, ext))
            continue

        cdir = './cache/'
        if not os.path.exists(cdir):
            os.mkdir(cdir)
        tcf = cdir + bn + '-cache.json'

        # load qald dataset and run TGM (or load cache)
        if os.path.exists(tcf):
            logger.info('Loading a cache file "{}"'.format(tcf))
            f = open(tcf, 'r')
            tmp = json.load(f)
            f.close()

        else:
            dataset = load_qald_dataset(fn, lang)
            templates = [run_tgm(d[0], lang, tgm_url) for d in dataset]

            tmp = [
                {
                    'qald-question': d[0],
                    'qald-type': d[1],
                    'qald-query': d[2],
                    'tgm-query': t[0]['query'],
                    'tgm-score': t[0]['score'],
                    'tgm-slots': t[0]['slots']
                }
                for d, t in zip(dataset, templates)
            ]

            f = open(tcf, 'w')
            f.write(json.dumps(tmp, sort_keys=True, indent=4))
            f.close()

        data.extend(tmp)
        logger.info('Prepared {} queries from "{}"'.format(len(tmp), fn))

    logger.info('Total data size: {}'.format(len(data)))

    return data

if __name__ == '__main__':
    fns = sys.argv[1:]

    data = prepare_data(fns)
