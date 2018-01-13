#!/bin/env python

"""
Module TGM Evaluator
"""

from sqa_evaluator import get_logger

import os
import json
import requests

import pyparsing
from rdflib.plugins import sparql

class TgmEvaluator:
    """
    Evaluator for specified TGM and language
    """

    logger     = get_logger('tgm_evaluator', debug=False)
    default_ns = {
        'rdf': 'http://xmlns.com/foaf/0.1/',
        'reds': 'http://www.w3.org/2000/01/rdf-schema#',
        'owl': 'http://www.w3.org/2002/07/owl#',
        'xsd': 'http://www.w3.org/2001/XMLSchema#',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'foaf': 'http://xmlns.com/foaf/0.1/',
        'obo': 'http://purl.obolibrary.org/obo/'
    }

    def __init__(self, name, url, language='en', cache=False, ns=dict()):
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
        self.data  = []

        # internal
        self.__cache     = cache
        self.__questions = set()
        self.__ns        = TgmEvaluator.default_ns
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
            TgmEvaluator.logger.warning('Input file "{}" is not a json file; skipping'.format(fn))
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
                qs.append({ 'nl_query': tmp_q, 'sparql': tmp_s })
                self.__questions.add(tmp_q)

        return qs

    def __run_tgm(self, query):
        """
        Run TGM using REST API

        :param query: NL query
        :return: result dict
        """

        tgm_in = '{{ "string": "{}", "language": "{}" }}'.format(query, self.lang)
        headers = { 'content-type': 'application/json' }

        try:
            r = requests.post(self.url, data=tgm_in, headers=headers)
        except UnicodeEncodeError:
            return { 'internal_error': True }

        if r.status_code == 200:
            raw = json.loads(r.text)
            if isinstance(raw, list):
                result = raw[0]
                result['length'] = len(raw)
            else:
                result = raw
                result['length'] = 1
        else:
            result = { 'message': r.text }

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
            return { 'syntax_error': True, 'error_message': str(pe) }

        result = { 'ask_query': False, 'triples': [] }
        
        def rec(p):
            if isinstance(p, sparql.algebra.CompValue):
                for k in p:
                    yield (k, p[k])
                    yield from rec(p[k])

        if a.name == 'AskQuery':
            result['ask_query'] = True

        for k, v in rec(a):
            if k == 'triples':
                result[k].extend([list(map(str, n)) for n in v])
            elif k == 'PV':
                result['targets'] = [str(t) for t in v]
            elif k in ('length', 'start'):
                result[k] = v

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
                dataset = self.__load_json_data(fn)
                parsed  = [self.__parse_sparql(d['sparql']) for d in dataset]
                origin  = [{ 'origin': d, 'origin_parsed': p } for d, p in zip(dataset, parsed)]

            # get tgm
            if tgm is None:
                templates = [self.__run_tgm(d['origin']['nl_query']) for d in origin]
                parsed    = [self.__parse_sparql(t.get('query', '')) for t in templates]
                tgm       = [{ 'tgm': t, 'tgm_parsed': p } for t, p in zip(templates, parsed)]

            # add data
            self.data.extend([{**o, **t} for o, t in zip(origin, tgm)])
            TgmEvaluator.logger.info('Prepared {} queries from "{}"'.format(len(tgm), fn))

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

    def eval(self):
        """
        Evaluate the TGM

        :return: result dict
        """

        result = {
            'all': len(self.data),
            'internal error': 0,
            'broken origin': 0,
            'type error (yes-no)': 0,
            'type error (factoid)': 0,
            'tgm fail': 0,
            'syntax error': 0,
            'non-connected target': 0
        }

        for q in self.data:
            # internal
            if q['tgm'].get('internal_error', False):
                q['eval'] = { 'bad': 'internal error', 'score': 0.0 }
                result['internal error'] += 1
                continue

            # status
            if q['tgm']['status'] != 200:
                q['eval'] = { 'bad': 'tgm fail', 'score': 0.0 }
                result['tgm fail'] += 1
                continue

            # SPARQL syntax
            if q['tgm_parsed'].get('syntax_error', False):
                q['eval'] = { 'bad': 'syntax error', 'score': 0.0 }
                result['syntax error'] += 1
                continue

            ask = q['tgm_parsed']['ask_query']

            # non-connected graph
            if not ask:
                nodes = [v for t in q['tgm_parsed']['triples'] for v in t]
                if False in map(lambda t: t in nodes, q['tgm_parsed']['targets']):
                    q['eval'] = { 'bad': 'non-connected target', 'score': 0.0 }
                    result['non-connected target'] += 1
                    continue

            # broken origin
            if q['origin_parsed'].get('syntax_error', False):
                q['eval'] = { 'bad': 'broken origin', 'score': 0.0 }
                result['broken origin'] += 1
                continue

            yes_no = q['origin_parsed']['ask_query']

            # question type
            if yes_no != ask:
                if yes_no:
                    q['eval'] = { 'bad': 'type error (yes-no)', 'score': 0.0 }
                    result['type error (yes-no)'] += 1
                else:
                    q['eval'] = { 'bad': 'type error (factoid)', 'score': 0.0 }
                    result['type error (factoid)'] += 1
                continue

            # all good
            q['eval'] = { 'score': 1.0 }

        return result
