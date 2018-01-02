#
# usage: python convert_cache.py {cache files}
#

import os
import sys
import json

def main():
    cache_files = sys.argv[1:]

    for fn in cache_files:
        data = json.load(open(fn))

        origin = [
            {
                'origin': q['origin'],
                'origin-qparse': q['qparse']['origin']
            }
            for q in data
        ]

        tgm = [
            {
                'tgm': q['tgm'],
                'tgm-qparse': q['qparse']['template']
            }
            for q in data
        ]

        # write
        wdir = './cache/'
        if not os.path.exists(wdir):
            os.mkdir(wdir)

        owf = wdir + fn.replace('-rocknrole', '-origin')
        twf = wdir + fn

        f = open(owf, 'w')
        f.write(json.dumps(origin, sort_keys=True, indent=4))
        f.close()

        f = open(twf, 'w')
        f.write(json.dumps(tgm, sort_keys=True, indent=4))
        f.close()

        # test
        #test = [{**o, **t} for o, t in zip(origin, tgm)]
        #f = open('test.json', 'w')
        #f.write(json.dumps(test, sort_keys=True, indent=4))
        #f.close()

if __name__ == '__main__':
    main()
