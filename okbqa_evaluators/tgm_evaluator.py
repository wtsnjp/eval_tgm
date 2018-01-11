#!/bin/env python

"""
Module TGM Evaluator
"""

from okbqa_evaluators import get_logger

import os
import json
import requests
import re
import subprocess

class TgmEvaluator:
    """
    Evaluator for specified TGM and language
    """

    logger = get_logger('tgm_evaluator', debug=True)

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
        self.data   = []

        # internal
        self.__cache = cache

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
        :return: a 2-tuple (status code, json data)
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

    def __run_qparse(self, query):
        """
        Run arq.qparse

        :param query: SPARQL query (or template)
        :return: result
        """

        command = ['qparse', '--print=op', '--fixup', query]

        qpr = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        result = {
            'return': qpr.returncode,
            'algebra': qpr.stdout.decode(),
            'error': qpr.stderr.decode()
        }

        return result

    def add_data(self, filenames):
        """
        Add data in specified files

        :param filenames: list of dataset filenames
        """

        for fn in filenames:
            origin, tgm = None, None

            # use cache file if exists
            if self.__cache:
                cdir = './cache/'
                if not os.path.exists(cdir):
                    os.mkdir(cdir)

                bn, ext = os.path.splitext(os.path.basename(fn))
                ocf = cdir + '{}-origin.json'.format(bn)
                tcf = cdir + '{}-{}.json'.format(bn, self.name)

                if os.path.exists(ocf):
                    TgmEvaluator.logger.info('Loading a cache "{}"'.format(ocf))
                    f = open(ocf, 'r')
                    origin = json.load(f)
                    f.close()

                if os.path.exists(tcf):
                    TgmEvaluator.logger.info('Loading a cache "{}"'.format(tcf))
                    f = open(tcf, 'r')
                    tgm = json.load(f)
                    f.close()

            # get origin
            if origin is None:
                dataset  = self.__load_json_data(fn)
                algebras = [self.__run_qparse(d[2]) for d in dataset]

                origin = [
                    {
                        'origin': {
                            'question': d[0],
                            'type': d[1],
                            'query': d[2],
                        },
                        'origin-qparse': a
                    }
                    for d, a in zip(dataset, algebras)
                ]

            # get tgm
            if tgm is None:
                templates = [self.__run_tgm(d['origin']['question']) for d in origin]
                algebras  = [self.__run_qparse(t[1].get('query', '')) for t in templates]

                tgm = [
                    {
                        'tgm': {
                            'status': t[0],
                            'query': t[1].get('query', ''),
                            'score': t[1].get('score', None),
                            'slots': t[1].get('slots', []),
                            'message': t[1].get('message', '')
                        },
                        'tgm-qparse': a
                    }
                    for t, a in zip(templates, algebras)
                ]

            # add data
            tmp = [{**o, **t} for o, t in zip(origin, tgm)]
            self.data.extend(tmp)
            TgmEvaluator.logger.info('Prepared {} queries from "{}"'.format(len(tmp), fn))

            # write cache
            if self.__cache:
                if not os.path.exists(ocf):
                    f = open(ocf, 'w')
                    f.write(json.dumps(origin, sort_keys=True, indent=4))
                    f.close()

                if not os.path.exists(tcf):
                    f = open(tcf, 'w')
                    f.write(json.dumps(tgm, sort_keys=True, indent=4))
                    f.close()

        TgmEvaluator.logger.info('Current data size: {}'.format(len(self.data)))

    def __parse_sse(self, sse):
        """
        Parse SSE

        :param query: SPARQL algebra (SSE)
        :return: 2-tuple (targets, triples)
        """

        sse = sse.replace('\n', '')
        sse = re.sub(' +', ' ', sse)

        m = re.search(r'\(project \((.*?)\)', sse)
        if m:
            targets = m.group(1).split(' ')
        else:
            targets = []

        triples = [
            { 's': m.group(1), 'p': m.group(2), 'o': m.group(3) }
            for m in re.finditer(r'\(triple (.*?) (.*?) (.*?)\)', sse)
        ]

        return (targets, triples)

    def eval(self):
        """
        Evaluate the TGM

        :return: result dict
        """

        result = {
            'all': len(self.data),
            'internal error': 0,
            'type error (yes-no)': 0,
            'type error (factoid)': 0,
            'tgm fail': 0,
            'syntax error': 0,
            'non-connected target': 0
        }

        # patterns
        ask_query = re.compile('(ASK|ask)')

        for q in self.data:
            # status
            if q['tgm']['status'] != 200:
                if q['tgm']['status'] == -1:
                    q['eval'] = { 'bad': 'internal error', 'score': 0.0 }
                    result['internal error'] += 1
                else:
                    q['eval'] = { 'bad': 'tgm fail', 'score': 0.0 }
                    result['tgm fail'] += 1

                continue

            # SPARQL syntax
            if q['tgm-qparse']['return'] != 0:
                q['eval'] = { 'bad': 'syntax error', 'score': 0.0 }
                result['syntax error'] += 1
                continue

            # question type
            yes_no = q['origin']['type'] == 'boolean'
            ask    = not ask_query.search(q['tgm']['query']) is None
            if yes_no != ask:
                if yes_no:
                    q['eval'] = { 'bad': 'type error (yes-no)', 'score': 0.0 }
                    result['type error (yes-no)'] += 1
                else:
                    q['eval'] = { 'bad': 'type error (factoid)', 'score': 0.0 }
                    result['type error (factoid)'] += 1
                continue

            # parse SSE
            t_targets, t_triples = self.__parse_sse(q['tgm-qparse']['algebra'])
            q['tgm-graph'] = { 'targets': t_targets, 'triples': t_triples }

            # non-connected graph
            if not ask:
                nodes = [v for t in t_triples for v in t.values()]
                if False in map(lambda t: t in nodes, t_targets):
                    q['eval'] = { 'bad': 'non-connected target', 'score': 0.0 }
                    result['non-connected target'] += 1
                    continue

            # all good
            q['eval'] = { 'score': 1.0 }

        return result
