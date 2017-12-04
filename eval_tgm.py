#
# usage: python eval_tgm.py {json file} ...
#

import sys
import json

from okbqa_evaluators.tgm_evaluator import TgmEvaluator

def save_errors(data):
    errors = [q for q in data if q['eval']['score'] < 1.0]
    f = open('./erros.json', 'w')
    f.write(json.dumps(errors, sort_keys=True, indent=4))
    f.close()

def main():
    fns      = sys.argv[1:]
    tgm_name = 'rocknrole'
    tgm_url  = 'http://ws.okbqa.org:1515/templategeneration/rocknrole'

    # prepare
    evaluator = TgmEvaluator(tgm_name, tgm_url, cache=True)
    evaluator.add_data(fns)

    # evaluate
    result = evaluator.eval()

    # show results
    for k, v in result.items():
        print('{}: {}'.format(k, v))
    #save_errors(evaluator.data)

if __name__ == '__main__':
    main()
