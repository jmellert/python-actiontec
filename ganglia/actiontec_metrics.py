#!/usr/bin/python

import os
import sys
import optparse
import time
import subprocess

from actiontec.statistics import Statistics

def parse_args():
    p = optparse.OptionParser()
    p.add_option('-a', '--address', default='192.168.1.1')
    p.add_option('-n', '--name')
    p.add_option('-u', '--user', default='admin')
    p.add_option('-p', '--password', default='password')

    return p.parse_args()

def gmetric(name, type, value, units='', slope='both',
        tmax=60, dmax=0, spoof=None, heartbeat=False):
    args = [str(x) for x in [
            '-n', name,
            '-t', type,
            '-v', value,
            '-u', units,
            '-s', slope,
            '-x', tmax,
            '-d', dmax,
            ]]

    if spoof is not None:
        args.extend(['-S', spoof])

    if heartbeat:
        args.append('-H')

    print 'gmetric', ' '.join(args)
    subprocess.call(['gmetric'] + args)

def main():
    opts, args = parse_args()
    if opts.name is None:
        opts.name = opts.address

    a = Statistics(opts.address, opts.user, opts.password)

    lastval = {}
    while True:
        start_time = time.time()

        cpus = a.cpus()
        gmetric('cpu_num', 'uint32', len(cpus),
                dmax=300,
                spoof='%s:%s' % (opts.address, opts.name))

        loadavg = a.loadavg()
        for x in ((0, 'one'), (1, 'five'), (2, 'fifteen')):
            gmetric('load_%s' % x[1], 'float', loadavg[x[0]],
                dmax=300,
                spoof='%s:%s' % (opts.address, opts.name))

        processes = a.processes()
        gmetric('proc_run', 'uint32', len(processes),
                dmax=300,
                spoof='%s:%s' % (opts.address, opts.name))
        gmetric('proc_total', 'uint32', len(processes),
                dmax=300,
                spoof='%s:%s' % (opts.address, opts.name))

        interfaces = a.interfaces()
        ifstats = a.ifstats()

        for iface,data in interfaces.items():
            if data['state'] not in ['running']:
                continue

            for name in ['rx_packets', 'rx_bytes', 'rx_errs', 'rx_drop',
                    'tx_packets', 'tx_bytes', 'tx_errs', 'tx_drop']:
                fqname = '%s_%s' % (iface, name)
                curval = ifstats[iface][name]
                rate = curval - lastval.get(fqname, curval)
                gmetric(fqname, 'uint32', rate,
                    dmax=300,
                    spoof='%s:%s' % (opts.address, opts.name))
                lastval[fqname] = curval

        time.sleep (60 - (time.time() - start_time))
    

if __name__ == '__main__':
    main()

