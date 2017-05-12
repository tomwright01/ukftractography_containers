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
#PBS -l nodes=1:ppn=8,mem=25gb
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
singularity run \
    -B {inDir}:/input \
    -B {outDir}:/output \
    {container_ukf} \
    {cmd_ukf}
singularity run \
    -B {outDir}:/input \
    -B {outDir}:/output \
    {container_wm} \
    {cmd_wm}
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

    def run(self, code, name="DTIPrep", logfile="output.$PBS_JOBID", errfile="error.$PBS_JOBID", slots=1):
        open(self.qs_n, 'w').write(JOB_TEMPLATE.format(script=code,
                                                       name=name,
                                                       logfile=logfile,
                                                       errfile=errfile,
                                                       slots=slots))
        os.chmod(self.qs_n, stat.S_IXUSR | stat.S_IWUSR | stat.S_IRUSR)
        logger.info('Submitting job')
        subprocess.call('qsub < ' + self.qs_n, shell=True)


def make_job(src_dir, dst_dir, log_dir, scan_name, mask_name, fa_val,
             cleanup=True):
    # create a job file from template and use qsub to submit
    cmd_ukf = """ \
    --numTensor 2 \
    --tracts /output/tensor_compare/fa_vals/{out_name} \
    --dwiFile /input/tensor_compare/orig_data/{scan_name} \
    --maskFile /input/tensor_compare/orig_data/{mask_name} \
    --minFA {fa_val}
    """

    cmd_wm = """
    wm_cluster_subject.py \
    /input/tensor_compare/fa_vals/{in_name} \
    /output/tensor_compare/fa_vals/{cluster_dir}
    """

    fiber_file = '2tensor_{}.vtk'.format(int(fa_val * 100))
    cluster_dir = 'clusters_{}'.format(int(fa_val * 100))

    cmd_ukf = cmd_ukf.format(out_name=fiber_file,
                             scan_name=scan_name,
                             mask_name=mask_name,
                             fa_val=fa_val)

    cmd_wm = cmd_wm.format(in_name=fiber_file,
                           cluster_dir=cluster_dir)

    code = CMD_TEMPLATE.format(inDir=src_dir,
                               outDir=dst_dir,
                               container_ukf=CONTAINER_UKF,
                               container_wm=CONTAINER_WM,
                               cmd_ukf=cmd_ukf,
                               cmd_wm=cmd_wm)

    with QJob(cleanup=cleanup) as qjob:
        #logfile = '{}:/tmp/output.$JOB_ID'.format(socket.gethostname())
        #errfile = '{}:/tmp/error.$JOB_ID'.format(socket.gethostname())
        logfile = os.path.join(log_dir, 'output.$PBS_JOBID')
        errfile = os.path.join(log_dir, 'error.$PBS_JOBID')
        qjob.run(code=code, logfile=logfile, errfile=errfile)


def launch_jobs():
    src_dir = '/imaging/scratch/kimel/twright/'
    dst_dir = '/imaging/scratch/kimel/twright/'
    log_dir = '/imaging/scratch/kimel/twright/tensor_compare/fa_vals/job_logs/'

    in_file = 'SPN01_CMH_0001_01_01_DTI60-1000_20_Ax-DTI-60plus5_QCed.nrrd'
    mask_file = 'SPN01_CMH_0001_01_01_DTI60-1000_20_Ax-DTI-60plus5_QCed_B0_threshold_masked.nrrd'

    fa_vals = np.arange(0.15, 0.25, 0.01)
    for fa_val in fa_vals:
        make_job(src_dir,
                 dst_dir,
                 log_dir,
                 in_file,
                 mask_file,
                 fa_val)

if __name__ == '__main__':
    launch_jobs()
