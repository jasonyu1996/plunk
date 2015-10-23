import collections;
import json;
import fcntl;

# Config = collections.namedtuple('Config', 'blog_name blog_subname nav_list');

def load_config(config_file):
    fin = open(config_file, 'r');
    fcntl.flock(fin, fcntl.LOCK_SH);
    config = json.loads(fin.read());
    fcntl.flock(fin, fcntl.LOCK_UN);
    fin.close();

    return config;

def dump_config(config, config_file):
    s = json.dumps(config, indent = 4);
    fout = open(config_file, 'w');
    fcntl.flock(fout, fcntl.LOCK_EX);
    fout.write(s);
    fcntl.flock(fout, fcntl.LOCK_UN);
    fout.close();


# print(load_config('../data/config.cnf'));
# for test

