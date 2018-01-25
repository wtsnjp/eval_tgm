#
# usage: python eval_tgm.py {json file} ...
#

import sys
import json

from sqa_evaluator.tgm_evaluator import TgmEvaluator

def dump_errors(name, level, data):
    fn = './dump/{}-{}.json'.format(name, level)
    crit = [q for q in data if q['eval'].get(level, False)]
    f = open(fn, 'w')
    f.write(json.dumps(crit, sort_keys=True, indent=4))
    f.close()

def dump_all(name, data):
    fn = './dump/{}-all.json'.format(name)
    f = open(fn, 'w')
    f.write(json.dumps(data, sort_keys=True, indent=4))
    f.close()

def show_results(r, ilist, clist, nlist):
    a = r['info']['all']

    if len(ilist) > 0:
        print('Information - {} questions'.format(a))
        for i in ilist:
            print('  {}: {}'.format(i, r['info'][i]))

    if len(clist) > 0:
        val = [r['critical'][i] for i in clist]
        noc = sum(val)
        par = noc / a * 100

        print('Critical - {} queries ({:.2f}%)'.format(noc, par))
        for k, v in zip(clist, val):
            print('  {}: {}'.format(k, v))

    if len(nlist) > 0:
        val = [r['notice'][i] for i in nlist]
        non = sum(val)
        par = non / a * 100

        print('Notice - {} queries ({:.2f}%)'.format(non, par))
        for k, v in zip(nlist, val):
            print('  {}: {}'.format(k, v))

def eval_tgm(name, url, fns):
    print('* Evaluating "{}"'.format(name))

    evaluator = TgmEvaluator(name, url, cache=True)

    evaluator.add_data(fns)
    evaluator.eval()

    ilist = ['broken origin', 'internal error']
    clist = ['tgm fail', 'syntax', 'question type (factoid)',
             'question type (yes-no)', 'non-connected target']
    nlist = ['wrong range']

    show_results(evaluator.result, ilist, clist, nlist)

    dump_errors(name, 'critical', evaluator.data)
    dump_errors(name, 'notice', evaluator.data)
    dump_all(name, evaluator.data)

def main():
    fns = list(reversed(sys.argv[1:]))

    eval_tgm('rocknrole', 'http://ws.okbqa.org:1515/templategeneration/rocknrole', fns)
    print()
    eval_tgm('lodqa', 'http://lodqa.org/template.json', fns)

if __name__ == '__main__':
    main()
