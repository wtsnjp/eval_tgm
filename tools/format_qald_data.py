#
# usage: python format_qald_data.py {qald directory}
#

import re
import os
import sys
import json

from xml.etree import ElementTree as ET

# questions should be removed
bad = ['Are the members of the Ramones that are not called Ramone?']

# patterns
spaces       = re.compile(r'\s+')
minus        = re.compile(r'SELECT DISTINCT \(\?h1-\?h2\) WHERE')
regex        = re.compile(r' FILTER \(NOT regex\(\?artistname,"Ramone"\)\)')
asas         = re.compile(r'(AS|as) \?number AS \?result')
count_before = re.compile(r'SELECT( DISTINCT|) COUNT(.*) WHERE \{')

def check_sparql(s):
    if s is None or s.strip() == 'OUT OF SCOPE':
        return False
    return True

def qdict(string, sparql):
    # normalize string
    string = string.strip()

    # normalize sparql
    sparql = spaces.sub(' ', sparql).strip()
    sparql = minus.sub('SELECT DISTINCT ((?h1 - ?h2) AS ?tgm_eval_result) WHERE', sparql)
    sparql = regex.sub(' FILTER (!(REGEX(?artistname, "Ramone")))', sparql)
    sparql = count_before.sub(r'SELECT (COUNT \2 AS ?result) WHERE {', sparql)
    sparql = asas.sub('AS ?number', sparql)

    return {
        'question': [{ 'language': 'en', 'string': string }],
        'query': { 'sparql': sparql }
    }

def xml_find_en_string(qn):
    for s in qn.findall('string'):
        if s.get('lang') == 'en':
            return s

def json_find_en_string(qs):
    for q in qs:
        if q['language'] == 'en':
            return q['string']

def write_file(wd, fn, qs):
    if not os.path.exists(wd):
        os.mkdir(wd)

    twf = wd + fn

    f = open(twf, 'w')
    f.write(json.dumps({'questions': qs}, sort_keys=True, indent=4))
    f.close()


def format_qald1(wd, qd):
    noq    = 0
    ddir   = '1/data/'
    dfiles = [
        'dbpedia-test.xml',
        'dbpedia-train.xml',
        'musicbrainz-test.xml',
        'musicbrainz-train.xml',
    ]

    for fn in dfiles:
        path = qd + ddir + fn
        bn, ext = os.path.splitext(os.path.basename(fn))

        # parse XML
        root = ET.parse(path).getroot()
        qs = [
            qdict(q.find('string').text, q.find('query').text)
            for q in root.findall('.//question')
            if check_sparql(q.find('query').text) and not (q.find('string').text.strip() in bad)
        ]
        noq += len(qs)

        write_file(wd, 'qald-1-{}.json'.format(bn), qs)

    print('Prepared {} questions from QALD-1'.format(noq))

def format_qald2(wd, qd):
    noq    = 0
    ddir   = '2/data/'
    dfiles = [
        'dbpedia-test.xml',
        'dbpedia-train.xml',
        'musicbrainz-test.xml',
        'musicbrainz-train.xml',
        'participants-challenge.xml'
    ]

    for fn in dfiles:
        path = qd + ddir + fn
        bn, ext = os.path.splitext(os.path.basename(fn))

        # parse XML
        root = ET.parse(path).getroot()
        qs = [
            qdict(q.find('string').text, q.find('query').text)
            for q in root.findall('.//question')
            if check_sparql(q.find('query').text)
        ]
        noq += len(qs)

        write_file(wd, 'qald-2-{}.json'.format(bn), qs)

    print('Prepared {} questions from QALD-2'.format(noq))

def format_qald3(wd, qd):
    noq    = 0
    ddir   = '3/data/'
    dfiles = [
        'dbpedia-test.xml',
        'dbpedia-train.xml',
        'musicbrainz-test.xml',
        'musicbrainz-train.xml',
        'esdbpedia-test.xml',
        'esdbpedia-train.xml'
    ]

    for fn in dfiles:
        path = qd + ddir + fn
        bn, ext = os.path.splitext(os.path.basename(fn))

        # parse XML
        root = ET.parse(path).getroot()
        qs = [
            qdict(xml_find_en_string(q).text, q.find('query').text)
            for q in root.findall('.//question')
            if check_sparql(q.find('query').text)
        ]
        noq += len(qs)

        write_file(wd, 'qald-3-{}.json'.format(bn), qs)

    print('Prepared {} questions from QALD-3'.format(noq))

def format_qald4(wd, qd):
    noq    = 0
    ddir   = '4/data/'
    dfiles = [
        'qald-4_multilingual_test.xml',
        'qald-4_multilingual_train.xml'
    ]

    for fn in dfiles:
        path = qd + ddir + fn
        bn, ext = os.path.splitext(os.path.basename(fn))

        # parse XML
        root = ET.parse(path).getroot()
        qs = [
            qdict(xml_find_en_string(q).text, q.find('query').text)
            for q in root.findall('.//question')
            if check_sparql(q.find('query').text)
        ]
        noq += len(qs)

        write_file(wd, '{}.json'.format(bn.replace('_', '-')), qs)

    print('Prepared {} questions from QALD-4'.format(noq))

def format_qald5(wd, qd):
    noq    = 0
    ddir   = '5/data/'
    dfiles = [
        'qald-5_test.xml',
        'qald-5_train.xml'
    ]

    for fn in dfiles:
        path = qd + ddir + fn
        bn, ext = os.path.splitext(os.path.basename(fn))

        # parse XML
        root = ET.parse(path).getroot()
        qs = [
            qdict(xml_find_en_string(q).text, q.find('query').text)
            for q in root.findall('.//question')
            if not q.find('query') is None and check_sparql(q.find('query').text)
        ]
        noq += len(qs)

        write_file(wd, '{}.json'.format(bn.replace('_', '-')), qs)

    print('Prepared {} questions from QALD-5'.format(noq))

def format_qald6(wd, qd):
    noq    = 0
    ddir   = '6/data/'
    dfiles = [
        'qald-6-test-multilingual.json',
        'qald-6-train-multilingual.json'
    ]

    for fn in dfiles:
        path = qd + ddir + fn

        # parse json
        qs = [
            qdict(json_find_en_string(q['question']), q['query']['sparql'])
            for q in json.load(open(path))['questions']
            if check_sparql(q['query'].get('sparql', None))
        ]
        noq += len(qs)

        write_file(wd, fn, qs)

    print('Prepared {} questions from QALD-6'.format(noq))

def format_qald7(wd, qd):
    noq    = 0
    ddir   = '7/data/'
    dfiles = [
        'qald-7-test-en-wikidata.json',
        'qald-7-test-multilingual.json',
        'qald-7-train-en-wikidata.json',
        'qald-7-train-largescale.json',
        'qald-7-train-multilingual.json'
    ]

    for fn in dfiles:
        path = qd + ddir + fn

        # parse json
        qs = [
            qdict(json_find_en_string(q['question']), q['query']['sparql'])
            for q in json.load(open(path))['questions']
            if check_sparql(q['query']['sparql'])
        ]
        noq += len(qs)

        write_file(wd, fn, qs)

    print('Prepared {} questions from QALD-7'.format(noq))

def main():
    qald_dir = sys.argv[1]
    data_dir = './data/'

    format_qald1(data_dir, qald_dir)
    format_qald2(data_dir, qald_dir)
    format_qald3(data_dir, qald_dir)
    format_qald4(data_dir, qald_dir)
    format_qald5(data_dir, qald_dir)
    format_qald6(data_dir, qald_dir)
    format_qald7(data_dir, qald_dir)

if __name__ == '__main__':
    main()
