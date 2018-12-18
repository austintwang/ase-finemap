from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals 
from __future__ import absolute_import

import os

from .job import main

curr_path = os.path.abspath(os.path.dirname(__file__))
data_dir = os.path.join(curr_path, "test_results", "jobs", "ENSG00000235478.1")
print(data_dir) ####
main(data_dir)

