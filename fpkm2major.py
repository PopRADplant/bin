#!/usr/bin/env python
desc="""Report major isoform for each gene for each condition.
"""
epilog="""Author: l.p.pryszcz@gmail.com
Mizerow, 6/05/2015
"""

import os, sys
from datetime import datetime
import numpy as np

def get_conditions(line):
    """Return conditions"""
    conditions = []
    lData = line.split('\t')
    for i in range(9, len(lData), 4):
        #strip("_FPKM")
        conditions.append(lData[i][:-5])
    return conditions

def parse_fpkm(handle, conditions):
    """Parse fpkm file from cufflinks and yield expression info
    for all trascripts of given gene. """
    pgid = None
    # sort in memory
    data = (l.split('\t') for l in handle)
    for lData in sorted(data, key=lambda x: x[3]): 
        # unload gene/transcript info
        tid, cc, nearest, gid, gene, tss, locus, length, cov = lData[:9]
        # store new gene info
        if pgid != gid:
            if pgid:
                yield pgid, transcripts, fpkms
            # reset
            transcripts = []
            fpkms = [[] for i in range(len(conditions))]
            # store new pgid
            pgid = gid            
        # add transcript info
        transcripts.append(tid)
        # and expression for each condition
        for ci, i in enumerate(range(9, len(lData), 4)):
            fpkm = float(lData[i])
            fpkms[ci].append(fpkm)
    #return conditions, genes, fpkms
    if pgid:
        yield pgid, transcripts, fpkms

def fpkm2major(handle, out, frac, minFpkm, link, verbose):
    """Parse expression and report major isoform for each condition"""
    # get conditions
    conditions = get_conditions(handle.readline())
    if verbose:
        sys.stderr.write("%s conditions: %s\n"%(len(conditions), ", ".join(conditions)))

    # get major isoforms
    header = "#\n#gene id\tno. of transcripts\tFPKM sum\t%s\t%s\n"
    out.write(header%('\t'.join(conditions), '\t'.join(map(str, range(5)))))
    line = "%s\t%s\t%.2f\t%s\t\t%s\n"
    j = k = 0
    for i, (gid, transcripts, fpkms) in enumerate(parse_fpkm(handle, conditions), 1):
        if len(transcripts)<2:
            continue
        k += 1
        #print gid, transcripts, fpkms
        # get max
        t2c = {t: 0 for t in transcripts}
        tmax = []
        for tfpkms in fpkms:
            _tfpkms = sorted(tfpkms, reverse=True)
            # report no major isoform if low expression or small difference
            if   _tfpkms[0] < minFpkm:
                major = 0
            elif (1-frac)*_tfpkms[0] < _tfpkms[1]:
                major = -1
            else:
                major = transcripts[tfpkms.index(_tfpkms[0])]
                t2c[major] += 1
            # 
            tmax.append(major)
        # get transcripts that appear most commonly as major
        stranscripts = sorted(t2c.iteritems(), key=lambda x: x[1]>0, reverse=1)
        mtranscripts = [t for t, c in filter(lambda x: x[1], stranscripts)]
        if len(mtranscripts)<2:
            continue
        j += 1
        # recode major isoforms as int
        majors = []
        for m in tmax:
            if m>1:
                majors.append(mtranscripts.index(m)+1)
            else:
                majors.append(m)
        # report
        fpkmSum = sum(sum(e) for e in fpkms)
        out.write(line%(_link(link, gid), len(transcripts), fpkmSum, "\t".join(map(str, majors)), "\t".join(mtranscripts)))
    if verbose:
        info = "%s genes\n %s genes with 2+ transcripts\n %s genes with 2+ major isoforms\n"
        sys.stderr.write(info%(i, k, j))

def _link(link, gid):
    """Return link"""
    if link:
        return link % tuple([gid]*link.count('%s'))
    return gid
        
def main():
    import argparse
    usage   = "%(prog)s -v" #usage=usage, 
    parser  = argparse.ArgumentParser(description=desc, epilog=epilog, \
                                      formatter_class=argparse.RawTextHelpFormatter)
  
    parser.add_argument('--version', action='version', version='1.0a')   
    parser.add_argument("-v", "--verbose", default=False, action="store_true",
                        help="verbose")    
    parser.add_argument("-i", "--fpkm", default=sys.stdin, type=file, 
                        help="isoforms.fpkm_tracking file [stdin]")
    parser.add_argument("-o", "--output", default=sys.stdout, type=argparse.FileType('w'), 
                        help="output stream   [stdout]")
    parser.add_argument("-f", "--frac", default=0.25, type=float, 
                        help="major isoform has to be larger at least -f than the second most expressed [%(default)s]")
    parser.add_argument("-m", "--minFPKM", default=1.0, type=float, 
                        help="min FPKM to report [%(default)s]")
    parser.add_argument("--link", default='=hyperlink("http://www.ensembl.org/Danio_rerio/Gene/Summary?db=core;g=%s", "%s")',
                        help="add hyperlink [%(default)s]")
    
    o = parser.parse_args()
    if o.verbose:
        sys.stderr.write("Options: %s\n"%str(o))
        
    fpkm2major(o.fpkm, o.output, o.frac, o.minFPKM, o.link, o.verbose)
 
if __name__=='__main__': 
    t0 = datetime.now()
    try:
        main()
    except KeyboardInterrupt:
        sys.stderr.write("\nCtrl-C pressed!      \n")
    except IOError as e:
        sys.stderr.write("I/O error({0}): {1}\n".format(e.errno, e.strerror))
    dt = datetime.now()-t0
    sys.stderr.write("#Time elapsed: %s\n"%dt)