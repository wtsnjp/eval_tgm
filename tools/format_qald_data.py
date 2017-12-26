#
# usage: python format_qald_data.py {qald directory}
#

import os
import sys
import json

from xml.etree import ElementTree as ET

def format_qald1(qd):
    print('There is no usefule data from QALD1')

def format_qald2(qd):
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
            {
                'answertype': q.get('answertype'),
                'question': [
                    {
                        'language': 'en',
                        'string': q.find('string').text.strip()
                    }
                ],
                'query': {
                    'sparql': q.find('query').text.strip()
                }
            }
            for q in root.findall('.//question')
        ]
        noq += len(qs)

        # write
        wdir = './data/'
        if not os.path.exists(wdir):
            os.mkdir(wdir)

        twf = wdir + 'qald-2-{}.json'.format(bn)

        f = open(twf, 'w')
        f.write(json.dumps({'questions': qs}, sort_keys=True, indent=4))
        f.close()

    print('Prepared {} questions from QALD2'.format(noq))

def format_qald3(qd):
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
        def find_string(qn):
            for s in qn.findall('string'):
                if s.get('lang') == 'en':
                    return s

        root = ET.parse(path).getroot()
        qs = [
            {
                'answertype': q.get('answertype'),
                'question': [
                    {
                        'language': 'en',
                        'string': find_string(q).text.strip()
                    }
                ],
                'query': {
                    'sparql': q.find('query').text.strip()
                }
            }
            for q in root.findall('.//question')
        ]
        noq += len(qs)

        # write
        wdir = './data/'
        if not os.path.exists(wdir):
            os.mkdir(wdir)

        twf = wdir + 'qald-3-{}.json'.format(bn)

        f = open(twf, 'w')
        f.write(json.dumps({'questions': qs}, sort_keys=True, indent=4))
        f.close()

    print('Prepared {} questions from QALD3'.format(noq))

def format_qald4(qd):
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
        def find_string(qn):
            for s in qn.findall('string'):
                if s.get('lang') == 'en':
                    return s

        root = ET.parse(path).getroot()
        qs = [
            {
                'answertype': q.get('answertype'),
                'question': [
                    {
                        'language': 'en',
                        'string': find_string(q).text.strip()
                    }
                ],
                'query': {
                    'sparql': q.find('query').text.strip()
                }
            }
            for q in root.findall('.//question')
        ]
        noq += len(qs)

        # write
        wdir = './data/'
        if not os.path.exists(wdir):
            os.mkdir(wdir)

        twf = wdir + '{}.json'.format(bn.replace('_', '-'))

        f = open(twf, 'w')
        f.write(json.dumps({'questions': qs}, sort_keys=True, indent=4))
        f.close()

    print('Prepared {} questions from QALD4'.format(noq))

def format_qald5(qd):
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
        def find_string(qn):
            for s in qn.findall('string'):
                if s.get('lang') == 'en':
                    return s

        root = ET.parse(path).getroot()
        qs = [
            {
                'answertype': q.get('answertype'),
                'question': [
                    {
                        'language': 'en',
                        'string': find_string(q).text.strip()
                    }
                ],
                'query': {
                    'sparql': q.find('query').text.strip()
                }
            }
            for q in root.findall('.//question')
            if not q.find('query') is None
        ]
        noq += len(qs)

        # write
        wdir = './data/'
        if not os.path.exists(wdir):
            os.mkdir(wdir)

        twf = wdir + '{}.json'.format(bn.replace('_', '-'))

        f = open(twf, 'w')
        f.write(json.dumps({'questions': qs}, sort_keys=True, indent=4))
        f.close()

    print('Prepared {} questions from QALD5'.format(noq))

def format_qald6(qd):
    noq    = 0
    ddir   = '6/data/'
    dfiles = [
        'qald-6-test-multilingual.json',
        'qald-6-train-multilingual.json'
    ]

    for fn in dfiles:
        path = qd + ddir + fn

        # parse json
        qs = json.load(open(path))
        noq += len(qs['questions'])

        # write
        wdir = './data/'
        if not os.path.exists(wdir):
            os.mkdir(wdir)

        twf = wdir + fn

        f = open(twf, 'w')
        f.write(json.dumps(qs, sort_keys=True, indent=4))
        f.close()

    print('Prepared {} questions from QALD6'.format(noq))

def format_qald7(qd):
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
        qs = json.load(open(path))
        noq += len(qs['questions'])

        # write
        wdir = './data/'
        if not os.path.exists(wdir):
            os.mkdir(wdir)

        twf = wdir + fn

        f = open(twf, 'w')
        f.write(json.dumps(qs, sort_keys=True, indent=4))
        f.close()

    print('Prepared {} questions from QALD7'.format(noq))

def main():
    qald_dir = sys.argv[1]

    format_qald1(qald_dir)
    format_qald2(qald_dir)
    format_qald3(qald_dir)
    format_qald4(qald_dir)
    format_qald5(qald_dir)
    format_qald6(qald_dir)
    format_qald7(qald_dir)

if __name__ == '__main__':
    main()
