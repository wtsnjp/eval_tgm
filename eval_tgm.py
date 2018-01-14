#
# usage: python eval_tgm.py {json file} ...
#

import sys
import json

from sqa_evaluator.tgm_evaluator import TgmEvaluator

def dump_errors(name, data):
    fn = './dump/{}-erros.json'.format(name)
    errors = [q for q in data if q['eval'].get('error', False)]
    f = open(fn, 'w')
    f.write(json.dumps(errors, sort_keys=True, indent=4))
    f.close()

def dump_all(name, data):
    fn = './dump/{}-all.json'.format(name)
    f = open(fn, 'w')
    f.write(json.dumps(data, sort_keys=True, indent=4))
    f.close()

def eval_tgm(name, url, fns):
    print('* Evaluating "{}"'.format(name))

    evaluator = TgmEvaluator(name, url, cache=True)

    evaluator.add_data(fns)
    evaluator.eval()

    # show results
    print('Infomaion:')
    for r in sorted(evaluator.result['info'].items(), key=lambda x: x[0]):
        print('  {}: {}'.format(r[0], r[1]))

    print('Errors:')
    for r in sorted(evaluator.result['error'].items(), key=lambda x: x[0]):
        print('  {}: {}'.format(r[0], r[1]))

    # dump data
    dump_errors(name, evaluator.data)
    dump_all(name, evaluator.data)

def main():
    fns = list(reversed(sys.argv[1:]))

    eval_tgm('rocknrole', 'http://ws.okbqa.org:1515/templategeneration/rocknrole', fns)
    print()
    eval_tgm('lodqa', 'http://lodqa.org/template.json', fns)

if __name__ == '__main__':
    main()
