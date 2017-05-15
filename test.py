#!/bin/env python

from __future__ import division
import subprocess
import os
import tempfile
import logging
import numpy as np
import stat

CONTAINER_UKF = '/imaging/home/kimel/twright/containers/UKFTRACTOGRAPHY/ukftractography.img'
CONTAINER_WM = '/imaging/home/kimel/twright/containers/WHITEMATTERANALYSIS/whitematteranalysis.img'
JOB_TEMPLATE = """
#####################################
#PBS -N {name}
#PBS -e {errfile}
#PBS -o {logfile}
#PBS -l nodes=1:ppn=2,mem=25gb
#PBS -l walltime=2:30:00
#PBS -m abe -M thomas.wright@camh.ca
#####################################
echo "------------------------------------------------------------------------"
echo "Job started on" `date` "on system" `hostname`
echo "------------------------------------------------------------------------"
{script}
echo "------------------------------------------------------------------------"
echo "Job ended on" `date`
echo "------------------------------------------------------------------------"
"""

CMD_TEMPLATE = """
sleep 25
"""


logging.basicConfig(level=logging.WARN,
                    format="[%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class QJob(object):
    def __init__(self, cleanup=True):
        self.cleanup = cleanup

    def __enter__(self):
        self.qs_f, self.qs_n = tempfile.mkstemp(suffix='.qsub')
        return self

    def __exit__(self, type, value, traceback):
        try:
            os.close(self.qs_f)
            if self.cleanup:
                os.remove(self.qs_n)
        except OSError:
            pass

    def run(self, code, name="DTIPrep",
            logfile="output.$PBS_JOBID", errfile="error.$PBS_JOBID",
            slots=1, depends=None):
        open(self.qs_n, 'w').write(JOB_TEMPLATE.format(script=code,
                                                       name=name,
                                                       logfile=logfile,
                                                       errfile=errfile,
                                                       slots=slots))
        os.chmod(self.qs_n, stat.S_IXUSR | stat.S_IWUSR | stat.S_IRUSR)
        logger.info('Submitting job')
        r = subprocess.call('qsub ' + self.qs_n)
        import pdb; pdb.set_trace()
        return r

if __name__ == '__main__':
    code = CMD_TEMPLATE
    with QJob() as qjob:
        qjob.run(code=code)
