#
# usage: python eval_tgm.py {json file} ...
#

import os
import sys
import json
import requests

# logging
from logging import getLogger, StreamHandler, Formatter, DEBUG

logger    = getLogger('eval_tgm')
handler   = StreamHandler()
formatter = Formatter('%(name)s %(levelname)s: %(message)s')

handler.setLevel(DEBUG)
handler.setFormatter(formatter)

logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False

# class
class TgmEvaluator:
    """
    Evaluator for specified TGM
    """

    def __init__(self, name, url, language='en', cache=False):
        """
        Initialize TGM Evaluator

        :param name: name of TGM
        :param url: REST API's endpoint of TGM
        :param language: (optional) language to use for evaluation
        :param cache: (optional) if True, cache file will be used
        """

        self.name  = name
        self.url   = url
        self.lang  = language
        self.cache = cache
        self.data  = []

    def __load_qald_dataset(self, fn):
        """
        Load QALD dataset (json file)

        :param fn: filename
        :return: list of 3-tuples (NL question, answertype, SPARQL query)
        """

        qs = []

        # check extention
        bn, ext = os.path.splitext(os.path.basename(fn))
        if ext != '.json':
            logger.warning('Input file "{}" is not a json file; skipping'.format(fn))
            return qs

        # get data from json file
        for e in json.load(open(fn))['questions']:
            tmp_q, tmp_a, tmp_s = None, None, None

            # NL question
            for q in e['question']:
                if q['language'] == self.lang:
                    tmp_q = q['string']
                    break

            # answertype
            tmp_a = e['answertype']

            # SPARQL query
            if 'sparql' in e['query']:
                tmp_s = e['query']['sparql']

            # use only questions which have all of 3 attributes
            if tmp_q and tmp_a and tmp_s:
                qs.append((tmp_q, tmp_a, tmp_s))

        return qs

    def __run_tgm(self, question):
        """
        Run TGM of OKBQA using REST API

        :param question: NL question
        :return: json data including {"query", "score", "slots"}
        """
        tgm_in = '{{ "string": "{}", "language": "{}" }}'.format(question, self.lang)
        r = requests.post(self.url, data=tgm_in)
        return json.loads(r.text)

    def add_data(self, filenames, provider='qald'):
        """
        Add data in specified files

        :param filenames: list of dataset filenames
        :param provider: (optional) name of dataset provider
        """

        for fn in filenames:
            # use cache file if exists
            if self.cache:
                cdir = './cache/'
                if not os.path.exists(cdir):
                    os.mkdir(cdir)

                bn, ext = os.path.splitext(os.path.basename(fn))
                tcf = cdir + '{}-{}.json'.format(bn, self.name)

                if os.path.exists(tcf):
                    logger.info('Loading a cache file "{}"'.format(tcf))
                    f = open(tcf, 'r')
                    tmp = json.load(f)
                    f.close()

                    self.data.extend(tmp)
                    continue

            # load qald dataset and run TGM
            if provider == 'qald':
                dataset = self.__load_qald_dataset(fn)
            templates = [self.__run_tgm(d[0]) for d in dataset]

            tmp = [
                {
                    'qald': {
                        'question': d[0],
                        'type': d[1],
                        'query': d[2],
                    },
                    self.name: {
                        'query': t[0]['query'],
                        'score': t[0]['score'],
                        'slots': t[0]['slots']
                    }
                }
                for d, t in zip(dataset, templates)
            ]

            self.data.extend(tmp)
            logger.info('Prepared {} queries from "{}"'.format(len(tmp), fn))

            # write cache
            if self.cache:
                f = open(tcf, 'w')
                f.write(json.dumps(tmp, sort_keys=True, indent=4))
                f.close()

        logger.info('Current data size: {}'.format(len(self.data)))

# run script functions
def main():
    fns      = sys.argv[1:]
    tgm_name = 'rocknrole'
    tgm_url  = 'http://ws.okbqa.org:1515/templategeneration/rocknrole'

    evaluator = TgmEvaluator(tgm_name, tgm_url, cache=True)
    evaluator.add_data(fns)

if __name__ == '__main__':
    main()
