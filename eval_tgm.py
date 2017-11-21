#
# usage: python eval_tgm.py {json file} ...
#

import os
import sys
import json
import requests

def err_print(err_type, msg):
    sys.stderr.write(err_type + ': ' + msg + '.\n')

def load_qald_dataset(fn):
    """
    Load QALD dataset from json file

    :param fn: filename
    :return: list of 3-tuples (NL question, answertype, SPARQL query)
    """
    return [(q['question'][0]['string'], q['answertype'], q['query']['pseudo'])
            for q in json.load(open(fn))['questions']]

def run_tgm(question, lang='en',
            tgm_url='http://ws.okbqa.org:1515/templategeneration/rocknrole'):
    """
    Run TGM of OKBQA using REST API

    :param question: NL question
    :param lang: (optional) language
    :param tgm_url: (optional) REST API's endpoint of TGM
    :return: json data including {"query", "score", "slots"}
    """
    tgm_in = '{ "string": "%s", "language": "%s" }' % (question, lang)
    r = requests.post(tgm_url, data=tgm_in)
    return json.loads(r.text)

def prepare_data(fns):
    """
    Prepare data for evaluation (use cache if exists)

    :param fn: list of filenames
    :return: list of dicts (whole data)
    """
    data = []

    for fn in fns:
        # cache file name
        bn, ext = os.path.splitext(os.path.basename(fn))
        if ext != '.json':
            err_print('Warning',
                      'Input file "' + bn + ext + '" is not a json file; skipping')
            continue
        tcf = './cache/' + bn + '-cache.json'

        # load qald dataset and run TGM (or load cache)
        if os.path.exists(tcf):
            err_print('Info', 'Loading a cache file "' + tcf + '"')
            f = open(tcf, 'r')
            tmp = json.load(f)
            f.close()

        else:
            dataset = load_qald_dataset(fn)
            templates = [run_tgm(d[0]) for d in dataset]

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
                if len(t) > 0
            ]

            f = open(tcf, 'w')
            f.write(json.dumps(tmp, sort_keys=True, indent=4))
            f.close()

        data.extend(tmp)
        err_print('Info', 'Prepared ' + str(len(tmp)) + ' queries from "' + fn + '"')

    return data

if __name__ == '__main__':
    fns = sys.argv[1:]

    data = prepare_data(fns)

    # debug
    print(json.dumps(data, sort_keys=True, indent=4))
