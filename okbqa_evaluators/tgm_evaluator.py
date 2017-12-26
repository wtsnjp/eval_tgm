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

    logger = get_logger('tgm_evaluator')

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

    def __load_json_data(self, fn):
        """
        Load json data

        :param fn: filename
        :return: list of 3-tuples (NL question, answertype, SPARQL query)
        """

        qs = []

        # check extention
        bn, ext = os.path.splitext(os.path.basename(fn))
        if ext != '.json':
            TgmEvaluator.logger.warning('Input file "{}" is not a json file; skipping'.format(fn))
            return qs

        # get data from json file
        TgmEvaluator.logger.info('Loading a file "{}"'.format(fn))
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
        headers = {'content-type': 'application/json'}
        try:
            r = requests.post(self.url, data=tgm_in, headers=headers)
        except UnicodeEncodeError:
            return (-1, {'message': 'UnicodeEncodeError'})
        if r.status_code == 200:
            result = json.loads(r.text)
            if isinstance(result, list):
                result = result[0]
        else:
            result = {'message': r.text}
        return (r.status_code, result)

    def add_data(self, filenames):
        """
        Add data in specified files

        :param filenames: list of dataset filenames
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
                    TgmEvaluator.logger.info('Loading a cache "{}"'.format(tcf))
                    f = open(tcf, 'r')
                    tmp = json.load(f)
                    f.close()

                    self.data.extend(tmp)
                    continue

            # load json data and run TGM
            dataset = self.__load_json_data(fn)
            templates = [self.__run_tgm(d[0]) for d in dataset]

            tmp = [
                {
                    'original': {
                        'question': d[0],
                        'type': d[1],
                        'query': d[2],
                    },
                    'tgm': {
                        'status': t[0],
                        'query': t[1].get('query', ''),
                        'score': t[1].get('score', None),
                        'slots': t[1].get('slots', []),
                        'message': t[1].get('message', '')
                    }
                }
                for d, t in zip(dataset, templates)
            ]

            self.data.extend(tmp)
            TgmEvaluator.logger.info('Prepared {} queries from "{}"'.format(len(tmp), fn))

            # write cache
            if self.cache:
                f = open(tcf, 'w')
                f.write(json.dumps(tmp, sort_keys=True, indent=4))
                f.close()

        TgmEvaluator.logger.info('Current data size: {}'.format(len(self.data)))

    def eval(self):
        """
        Evaluate the TGM

        :return: result dict
        """

        result = {'type_errors': 0, 'tgm_fail': 0}

        # patterns
        ask_query = re.compile('(ASK|ask)')

        for q in self.data:
            # status
            if q['tgm']['status'] != 200:
                q['eval'] = { 'bad': 'tgm_fail', 'score': 0.0 }
                result['tgm_fail'] += 1
                continue

            # question type
            yes_no = q['original']['type'] == 'boolean'
            ask    = not ask_query.search(q['tgm']['query']) is None
            if yes_no != ask:
                q['eval'] = { 'bad': 'type_error', 'score': 0.0 }
                result['type_errors'] += 1
                continue

            # all good
            q['eval'] = { 'score': 1.0 }

        return result
