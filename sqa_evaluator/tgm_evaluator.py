#!/bin/env python
"""
Module TGM Evaluator
"""

from sqa_evaluator import get_logger

import os
import json
import requests
from functools import reduce

import pyparsing
from rdflib.plugins import sparql


class TgmEvaluator:
    """
    Evaluator for specified TGM and language
    """

    logger = get_logger('tgm_evaluator', debug=False)
    default_ns = {
        'rdf': 'http://xmlns.com/foaf/0.1/',
        'reds': 'http://www.w3.org/2000/01/rdf-schema#',
        'owl': 'http://www.w3.org/2002/07/owl#',
        'xsd': 'http://www.w3.org/2001/XMLSchema#',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'foaf': 'http://xmlns.com/foaf/0.1/',
        'obo': 'http://purl.obolibrary.org/obo/',
        'res': 'http://dbpedia.org/resource/',
        'onto': 'http://dbpedia.org/ontology/',
        'prop': 'http://dbpedia.org/property/',
    }

    def __init__(self, name, url, language='en', cache=False, ns=dict()):
        """
        Initialize TGM Evaluator

        :param name: name of TGM
        :param url: REST API's endpoint of TGM
        :param language: (optional) language to use for evaluation
        :param cache: (optional) if True, cache file will be used
        """

        self.name = name
        self.url = url
        self.lang = language
        self.data = []

        # internal
        self.__cache = cache
        self.__questions = set()
        self.__ns = TgmEvaluator.default_ns
        self.__ns.update(ns)

    def __load_json_data(self, fn):
        """
        Load json data

        :param fn: filename
        :return: result dict
        """

        qs = []

        # check extention
        bn, ext = os.path.splitext(os.path.basename(fn))
        if ext != '.json':
            TgmEvaluator.logger.warning(
                'Input file "{}" is not a json file; skipping'.format(fn))
            return qs

        # get data from json file
        TgmEvaluator.logger.info('Loading a file "{}"'.format(fn))
        for e in json.load(open(fn)).get('questions', dict()):
            tmp_q, tmp_s = None, None

            # NL query (question)
            for q in e.get('question', dict()):
                if q.get('language', None) == self.lang:
                    tmp_q = q.get('string', None)
                    break

            # SPARQL query
            tmp_s = e.get('query', dict()).get('sparql', None)

            # use only *good* questions
            if tmp_q and tmp_s and not tmp_q in self.__questions:
                qs.append({
                    'nl_query': tmp_q,
                    'sparql': tmp_s,
                    'source': bn + ext
                })
                self.__questions.add(tmp_q)

        return qs

    def __run_tgm(self, query):
        """
        Run TGM using REST API

        :param query: NL query
        :return: result dict
        """

        tgm_in = {'string': query, 'language': self.lang}
        headers = {'content-type': 'application/json'}

        try:
            r = requests.post(
                self.url,
                headers=headers,
                data=json.dumps(tgm_in).encode('utf-8'))
        except UnicodeEncodeError:
            return {'internal_error': True}

        if r.status_code == 200:
            raw = json.loads(r.text)
            if isinstance(raw, list):
                result = raw[0]
                result['length'] = len(raw)
            else:
                result = raw
                result['length'] = 1
        else:
            result = {'message': r.text}

        result['status'] = r.status_code

        return result

    def __parse_sparql(self, query):
        """
        Parse SPARQL with rdflib

        :param query: SPARQL query (or template)
        :return: result dict
        """

        try:
            p = sparql.parser.parseQuery(query)
            a = sparql.algebra.translateQuery(p, initNs=self.__ns).algebra
        except pyparsing.ParseException as pe:
            return {'syntax_error': True, 'error_message': str(pe)}

        result = {'ask_query': False, 'triples': [], 'binds': dict()}

        def rec(p):
            if isinstance(p, sparql.algebra.CompValue):
                for k in p:
                    yield (k, p[k])
                    yield from rec(p[k])

        if a.name == 'AskQuery':
            result['ask_query'] = True

        var1, var2 = False, False

        for k, v in rec(a):
            if k == 'triples':
                result[k].extend([list(map(str, n)) for n in v])
            elif k == 'PV':
                result['targets'] = [str(t) for t in v]
            elif k == 'var':
                var1 = str(v)
            elif k == 'A':
                var2 = str(v[0].vars)
            elif k in ('length', 'start'):
                result[k] = v

        if var1 and var2:
            result['binds'][var1] = var2

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
                    TgmEvaluator.logger.info(
                        'Loading a cache "{}"'.format(ocf))
                    f = open(ocf, 'r')
                    origin = json.load(f)
                    f.close()

                if os.path.exists(tcf):
                    TgmEvaluator.logger.info(
                        'Loading a cache "{}"'.format(tcf))
                    f = open(tcf, 'r')
                    tgm = json.load(f)
                    f.close()

            # get origin
            if origin is None:
                dataset = self.__load_json_data(fn)
                parsed = [self.__parse_sparql(d['sparql']) for d in dataset]
                origin = [{
                    'origin': d,
                    'origin_parsed': p
                } for d, p in zip(dataset, parsed)]

            # get tgm
            if tgm is None:
                templates = [
                    self.__run_tgm(d['origin']['nl_query']) for d in origin
                ]
                parsed = [
                    self.__parse_sparql(t.get('query', '')) for t in templates
                ]
                tgm = [{
                    'tgm': t,
                    'tgm_parsed': p
                } for t, p in zip(templates, parsed)]

            # add data
            self.data.extend([{**o, **t} for o, t in zip(origin, tgm)])
            TgmEvaluator.logger.info('Prepared {} queries from "{}"'.format(
                len(tgm), fn))

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

        TgmEvaluator.logger.info('Current data size: {}'.format(
            len(self.data)))

    def __update(self, i, level, reason):
        self.result[level][reason] += 1
        self.data[i]['eval'].update({level: reason})

    def eval(self):
        """
        Evaluate the TGM

        :return: result dict
        """

        self.result = {
            'info': {
                'all': len(self.data),
                'internal error': 0,
                'broken origin': 0,
                'yes-no question': 0,
                'factoid question': 0,
                'range specified': 0
            },
            'critical': {
                'question type (yes-no)': 0,
                'question type (factoid)': 0,
                'tgm fail': 0,
                'syntax': 0,
                'disconnected target': 0
            },
            'notice': {
                'wrong range': 0,
                'disconnected triple': 0
            },
            'ok': {
                'question type (yes-no)': 0,
                'question type (factoid)': 0,
                'disconnected target': 0,
                'wrong range': 0,
                'disconnected triple': 0
            }
        }

        for i in range(len(self.data)):
            # initialize
            self.data[i]['eval'] = dict()

            t = self.data[i]['tgm']
            op = self.data[i]['origin_parsed']
            tp = self.data[i]['tgm_parsed']

            # broken origin
            broken = False
            if op.get('syntax_error', False):
                self.__update(i, 'info', 'broken origin')
                broken = True

            # collect origin info
            if not broken:
                yes_no = op['ask_query']
                if yes_no:
                    self.result['info']['yes-no question'] += 1
                else:
                    self.result['info']['factoid question'] += 1

                o_len, o_off = op.get('length', -1), op.get('start', -1)
                if o_len >= 0:
                    self.result['info']['range specified'] += 1

            # internal
            if t.get('internal_error', False):
                self.__update(i, 'info', 'internal error')
                continue

            # status
            if t['status'] != 200:
                self.__update(i, 'critical', 'tgm fail')
                continue

            # SPARQL syntax
            if tp.get('syntax_error', False):
                self.__update(i, 'critical', 'syntax')
                continue

            ask = tp['ask_query']

            if broken:
                continue

            # question type
            if yes_no != ask:
                if yes_no:
                    self.__update(i, 'critical', 'question type (yes-no)')
                else:
                    self.__update(i, 'critical', 'question type (factoid)')
                continue
            else:
                if yes_no:
                    self.result['ok']['question type (yes-no)'] += 1
                else:
                    self.result['ok']['question type (factoid)'] += 1

            # disconnected target
            if not ask:
                nodes = [v for t in tp['triples'] for v in t]
                targets = [tp['binds'].get(t, t) for t in tp['targets']]
                if False in map(lambda t: t in nodes, targets):
                    self.__update(i, 'critical', 'disconnected target')
                    continue
                else:
                    self.result['ok']['disconnected target'] += 1

            # length and offset
            if o_len >= 0:
                t_len, t_off = tp.get('length', -1), tp.get('start', -1)
                if o_len != t_len or o_off != t_off:
                    self.__update(i, 'notice', 'wrong range')
                    continue
                else:
                    self.result['ok']['wrong range'] += 1

            # disconnected triples
            if not ask:
                seen = []
                for t in tp['triples']:
                    idx = [
                        k for k in [
                            j
                            if True in [n in [u for u in seen[j]]
                                        for n in t] else None
                            for j in range(len(seen))
                        ] if not k is None
                    ]
                    if len(idx) > 0:
                        tmp = reduce(lambda a, b: a | b,
                                     [seen[j] for j in idx] + [set(t)])
                        for j in sorted(idx, reverse=True):
                            del seen[j]
                        seen.append(tmp)
                    else:
                        seen.append(set(t))

                if False in [True in [u in targets for u in s] for s in seen]:
                    self.__update(i, 'notice', 'disconnected triple')
                    continue
                else:
                    self.result['ok']['disconnected triple'] += 1

            # good
            self.data[i]['eval']['info'] = 'good'
