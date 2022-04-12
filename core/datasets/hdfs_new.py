# https://drive.google.com/uc?id=1yVWq065qjyKM7TcAF1aIkfc5jVyPPcQM
from os.path import exists
from utils.Drain import LogParser
import gdown

output_path = "../data/hdfs/HDFS.log"
# https://drive.google.com/uc?id=1yVWq065qjyKM7TcAF1aIkfc5jVyPPcQM
# https://drive.google.com/file/d/1CPoIS5-ICN_lXUKv-adcY977A_AN4B3u/view?usp=sharing
url = 'https://drive.google.com/uc?id=1yVWq065qjyKM7TcAF1aIkfc5jVyPPcQM'
if not exists(output_path):
    # mkdir(join("../data/hdfs"))
    gdown.download(url, output_path, quiet=False)

import sys

sys.path.append('../')

input_dir = "../data/hdfs/"
output_dir = "../data/hdfs/"
log_file = 'HDFS.log'
log_format = "<Date> <Time> <Pid> <Level> <Component>: <Content>"

# Regular expression list for optional preprocessing (default: [])
regex = [
    r'blk_(|-)[0-9]+',  # block id
    r'(/|)([0-9]+\.){3}[0-9]+(:[0-9]+|)(:|)',  # IP
    r'(?<=[^A-Za-z0-9])(\-?\+?\d+)(?=[^A-Za-z0-9])|[0-9]+$',  # Numbers
]
st = 0.5  # Similarity threshold
depth = 2  # Depth of all leaf nodes

parser = LogParser(log_format, indir=input_dir, outdir=output_dir, depth=depth, st=st, rex=regex)
parser.parse(log_file)
