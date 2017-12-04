#!/bin/env python

"""
Module TGM Evaluator
"""

from okbqa_evaluators import get_logger

import os
import json
import requests
import re

class TgmEvaluator:
    """
    Evaluator for specified TGM and language
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

        # internal
        self.data   = []
        self.logger = get_logger(__name__)

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
            self.logger.warning('Input file "{}" is not a json file; skipping'.format(fn))
            return qs

        # get data from json file
        self.logger.info('Loading QALD dataset "{}"'.format(fn))
        for e in json.load(open(fn)).get('questions', dict()):
            tmp_q, tmp_a, tmp_s = None, None, None

            # NL question
            for q in e.get('question', dict()):
                if q.get('language', None) == self.lang:
                    tmp_q = q.get('string', None)
                    break

            # answertype
            tmp_a = e.get('answertype', None)

            # SPARQL query
            tmp_s = e.get('query', dict()).get('sparql', None)

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
                    self.logger.info('Loading a cache file "{}"'.format(tcf))
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
            self.logger.info('Prepared {} queries from "{}"'.format(len(tmp), fn))

            # write cache
            if self.cache:
                f = open(tcf, 'w')
                f.write(json.dumps(tmp, sort_keys=True, indent=4))
                f.close()

        self.logger.info('Current data size: {}'.format(len(self.data)))

    def eval(self):
        """
        Evaluate the TGM

        :return: result dict
        """

        result = {'type_errors': 0}

        # patterns
        ask_query = re.compile('(ASK|ask)')

        for q in self.data:
            # question type
            yes_no = q['qald']['type'] == 'boolean'
            ask    = not ask_query.search(q[self.name]['query']) is None
            if yes_no != ask:
                q['eval'] = { 'bad': 'type_error', 'score': 0.0 }
                result['type_errors'] += 1
                continue

            # all good
            q['eval'] = { 'score': 1.0 }

        return result
