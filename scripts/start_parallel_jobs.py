#!/usr/bin/env python
# File created on 10 Mar 2010
from __future__ import division

__author__ = "Greg Caporaso"
__copyright__ = "Copyright 2011-2013, The PICRUSt Project"
__credits__ = ["Greg Caporaso","Morgan Langille"]
__license__ = "GPL"
__version__ = "0.9.1-dev"
__maintainer__ = "Greg Caporaso"
__email__ = "gregcaporaso@gmail.com"
__status__ = "Development"
 

#from qiime.util import make_option
#from qiime.util import parse_command_line_parameters

from cogent.util.option_parsing import parse_command_line_parameters, make_option

from subprocess import Popen
from os import makedirs, chmod, getenv, remove
from os.path import exists
from shutil import rmtree
from stat import S_IRWXU
from picrust.parallel import grouper
from math import ceil

#from qiime.util import load_qiime_config

#qiime_config = load_qiime_config()


script_info = {}
script_info['brief_description'] = "Starts multiple jobs in parallel on multicore or multiprocessor systems."
script_info['script_description'] = "This script is designed to start multiple jobs in parallel on systems with no queueing system, for example a multiple processor or multiple core laptop/desktop machine. This also serves as an example 'cluster_jobs' which users can use a template to define scripts to start parallel jobs in their environment."
script_info['script_usage'] = [\
 ("Example",\
 "Start each command listed in test_jobs.txt in parallel. The run id for these jobs will be RUNID. ",\
 "%prog -ms test_jobs.txt RUNID")]
script_info['output_description']= "No output is created."
script_info['required_options'] = []
script_info['optional_options'] = [\
 make_option('-m','--make_jobs',action='store_true',\
         help='make the job files [default: %default]'),\
 make_option('-s','--submit_jobs',action='store_true',\
         help='submit the job files [default: %default]'),\
 make_option('-n','--num_jobs',action='store',type='int',\
             help='Number of jobs to group commands into. [default: %default]',\
                default=4)\
]
script_info['version'] = __version__
script_info['disallow_positional_arguments'] = False

def write_job_files(output_dir,commands,run_id,num_jobs=4):
    jobs_dir = '%s/jobs/' % output_dir
    job_fps = []
    if not exists(jobs_dir):
        try:
            makedirs(jobs_dir)
        except OSError,e:
            raise OSError, "Error creating jobs directory in working dir: %s" % output_dir +\
            " (specified in qiime_config). Do you have write access?. "+\
            "Original error message follows:\n%s" % str(e)
        paths_to_remove = [jobs_dir]
    else:
        # point paths_to_remove at job_fps
        paths_to_remove = job_fps
    
    # This is messy right now as our clusters (bmf, bmf2) require us to
    # start and exit a shell for some reason which we haven't figured out. 
    # Running these commands as parallel shell scripts gets screwed up by 
    # this. For the time-being, I'm stripping this out here. Once the new 
    # clusters are up, I'm going to move the wrapping of commands in 
    # bash/exit to the cluster_jobs script. At that point this function
    # will be greatly simplified.
    ignored_subcommands = {}.fromkeys(['/bin/bash','exit'])

    #calculate the number of commands to put in each job
    num_commands_per_job=int(ceil(len(commands)/float(num_jobs)))

    for i,command_group in enumerate(grouper(commands,num_commands_per_job,'')):
        job_fp = '%s/%s%d' % (jobs_dir, run_id, i)
        f = open(job_fp,'w')
        for command in command_group:
            f.write('\n'.join([subcommand \
              for subcommand in command.split(';') 
              if subcommand.strip() not in ignored_subcommands]))
        f.close()
        chmod(job_fp, S_IRWXU)
        job_fps.append(job_fp)
    
    return job_fps, paths_to_remove

def run_commands(output_dir,commands,run_id,submit_jobs,keep_temp,num_jobs=4):
    """
    """
    # Popen is not a big fan of how we join commands with semi-colons,
    # so each command is written to a shell script which is then called 
    # by Popen
    job_fps, paths_to_remove = write_job_files(output_dir,commands,run_id,num_jobs=num_jobs)
    
    # Call the jobs
    if submit_jobs:
        for job_fp in job_fps:
            Popen(['/bin/sh', job_fp])
    
    # clean up the shell scripts that were created
    if not keep_temp:
        for p in paths_to_remove:
            try:
                # p is file
                remove(p)
            except OSError:
                # p is directory
                rmtree(p)
    return

def main():
    option_parser, opts, args =\
       parse_command_line_parameters(**script_info)
       
    if opts.submit_jobs and not opts.make_jobs:
        option_parser.error('Must pass -m if passing -s. (Sorry about this, '+\
        'it\'s for backwards-compatibility.)') 

    min_args = 2
    if len(args) < min_args:
       option_parser.error('Exactly two arguments are required.')
       
    output_dir = './'
    run_commands(output_dir,open(args[0]).readlines(),args[1],\
     submit_jobs=opts.submit_jobs,\
     keep_temp=True,num_jobs=opts.num_jobs)


if __name__ == "__main__":
    main()
