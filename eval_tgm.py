#
# usage: python eval_tgm.py {json file} ...
#

import os
import sys
import json

from sqa_evaluator.tgm_evaluator import TgmEvaluator


def dump_errors(name, level, data):
    ddir = './dump/'
    if not os.path.exists(ddir):
        os.mkdir(ddir)

    fn = ddir + '{}-{}.json'.format(name, level)
    crit = [q for q in data if q['eval'].get(level, False)]
    f = open(fn, 'w')
    f.write(json.dumps(crit, sort_keys=True, indent=4))
    f.close()


def dump_all(name, data):
    ddir = './dump/'
    if not os.path.exists(ddir):
        os.mkdir(ddir)

    fn = ddir + '{}-all.json'.format(name)
    f = open(fn, 'w')
    f.write(json.dumps(data, sort_keys=True, indent=4))
    f.close()


def show_results(r, ilist, clist, nlist, detail=True):
    a = r['info']['all']

    if len(ilist) > 0:
        print('Information - {} questions'.format(a))
        for i in ilist:
            if i == 'range specified':
                print('    {}: {}'.format(i, r['info'][i]))
            else:
                print('  {}: {}'.format(i, r['info'][i]))

    if a < 1:
        return

    def show_details(r, ls, val, detail):
        for k, v in zip(ls, val):
            tmp_a = r['ok'].get(k, 0) + v
            if detail and k in r['ok']:
                if tmp_a > 0:
                    tmp_par = v / tmp_a * 100
                    print('  {}: {} [out of {} ({:.2f}%)]'.format(
                        k, v, tmp_a, tmp_par))
                else:
                    print('  {}: {} [out of {}]'.format(k, v, tmp_a))
            else:
                print('  {}: {}'.format(k, v))

    if len(clist) > 0:
        val = [r['critical'][i] for i in clist]
        noc = sum(val)
        par = noc / a * 100

        print('Critical - {} queries ({:.2f}%)'.format(noc, par))
        show_details(r, clist, val, detail)

    if len(nlist) > 0:
        val = [r['notice'][i] for i in nlist]
        non = sum(val)
        par = non / a * 100

        print('Notice - {} queries ({:.2f}%)'.format(non, par))
        show_details(r, nlist, val, detail)


def eval_tgm(name, url, fns):
    print('* Evaluating "{}"'.format(name))

    evaluator = TgmEvaluator(name, url, cache=True)

    evaluator.add_data(fns)
    evaluator.eval()

    ilist = [
        'broken origin', 'internal error', 'yes-no question',
        'factoid question', 'range specified'
    ]
    clist = [
        'tgm fail', 'syntax', 'question type (factoid)',
        'question type (yes-no)', 'disconnected target'
    ]
    nlist = ['wrong range', 'disconnected triple']

    show_results(evaluator.result, ilist, clist, nlist, detail=True)

    dump_errors(name, 'critical', evaluator.data)
    dump_errors(name, 'notice', evaluator.data)
    dump_all(name, evaluator.data)


def main():
    fns = list(reversed(sys.argv[1:]))

    eval_tgm('rocknrole',
             'http://ws.okbqa.org:1515/templategeneration/rocknrole', fns)
    print()
    eval_tgm('lodqa', 'http://lodqa.org/template.json', fns)


if __name__ == '__main__':
    main()
