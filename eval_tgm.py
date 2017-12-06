#
# usage: python eval_tgm.py {json file} ...
#

import sys
import json

from okbqa_evaluators.tgm_evaluator import TgmEvaluator

def save_errors(name, data):
    fn = './erros-{}.json'.format(name)
    errors = [q for q in data if q['eval']['score'] < 1.0]
    f = open(fn, 'w')
    f.write(json.dumps(errors, sort_keys=True, indent=4))
    f.close()

def eval_tgm(name, url, fns):
    print('* Evaluating "{}"'.format(name))

    # prepare
    evaluator = TgmEvaluator(name, url, cache=True)
    evaluator.add_data(fns)

    # evaluate
    result = evaluator.eval()

    # show results
    for r in sorted(result.items(), key=lambda x: x[0]):
        print('{}: {}'.format(r[0], r[1]))
    save_errors(name, evaluator.data)

def main():
    fns = sys.argv[1:]

    eval_tgm('rocknrole', 'http://ws.okbqa.org:1515/templategeneration/rocknrole', fns)
    print()
    eval_tgm('lodqa', 'http://52.199.182.91:38401/template.json', fns)

if __name__ == '__main__':
    main()
