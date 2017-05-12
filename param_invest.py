#!/bin/env python

from __future__ import division
import subprocess
import os
import tempfile
import logging
import numpy as np

CONTAINER = '/imaging/home/kimel/twright/containers/UKFTRACTOGAPHY/ukftractography.img'

JOB_TEMPLATE = """
#####################################
#PBS -N {name}
#PBS -e {errfile}
#PBS -o {logfile}
#PBS -l nodes=1:ppn=8,mem=25gb
#PBS -l walltime=4:00:00
#PBS -m twright -M thomas.wright@camh.ca
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
singularity run \
    -B {inDir}:/input \
    -B {outDir}:/output \
    {container} \
    {cmd}
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

    def run(self, code, name="DTIPrep", logfile="output.$JOB_ID", errfile="error.$JOB_ID", cleanup=True, slots=1):
        open(self.qs_n, 'w').write(JOB_TEMPLATE.format(script=code,
                                                       name=name,
                                                       logfile=logfile,
                                                       errfile=errfile,
                                                       slots=slots))
        logger.info('Submitting job')
        subprocess.call('qsub < ' + self.qs_n, shell=True)


def make_job(src_dir, dst_dir, log_dir, scan_name, mask_name, fa_val, out_name, cleanup=True):
    # create a job file from template and use qsub to submit
    code = """
    module load PYTHON/2.7.13
    ukftractography --numTensor 2 \
    --tracts /output/{out_name} \
    --dwiFile /input/{scan_name} \
    --maskFile /input/{mask_name} \
    --minFA {fa_val}
    """
    code = code.format(out_name=out_name,
                       scan_name=scan_name,
                       mask_name=mask_name,
                       fa_val=fa_val)

    with QJob() as qjob:
        #logfile = '{}:/tmp/output.$JOB_ID'.format(socket.gethostname())
        #errfile = '{}:/tmp/error.$JOB_ID'.format(socket.gethostname())
        logfile = os.path.join(log_dir, 'output.$JOB_ID')
        errfile = os.path.join(log_dir, 'error.$JOB_ID')
        qjob.run(code=code, logfile=logfile, errfile=errfile)


def launch_jobs():
    src_dir = '/imaging/scratch/kimel/twright/tensor_compare/orig_data/'
    dst_dir = '/imaging/scratch/kimel/twright/tensor_compare/fa_vals/'
    log_dir = '/imaging/scratch/kimel/twright/tensor_compare/fa_vals/job_logs/'

    in_file = 'SPN01_CMH_0001_01_01_DTI60-1000_20_Ax-DTI-60plus5_QCed.nrrd'
    mask_file = 'SPN01_CMH_0001_01_01_DTI60-1000_20_Ax-DTI-60plus5_QCed_B0_threshold_masked.nrrd'

    fa_vals = np.arange(0.15, 0.25, 0.01)
    for fa_val in fa_vals:
        dest_file = '2tensor_{}.vtk'.format(int(fa_val * 100))
        make_job(src_dir,
                 dst_dir,
                 log_dir,
                 in_file,
                 mask_file,
                 fa_val,
                 dest_file)

if __name__ == '__main__':
    launch_jobs()
