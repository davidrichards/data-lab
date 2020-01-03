import os,pickle,re,shutil,sys,zlib

from configparser import ConfigParser
from contextlib import contextmanager
import datetime as dt
from datetime import datetime
from functools import partial,lru_cache
from pathlib import Path
import pathlib

import google.protobuf
import numpy as np

import data_lab.prototypes.training_pb2 as training_prototypes
import data_lab.object_store.noop as noop_object_store
import data_lab.develop.utils as utils

@contextmanager
def check_raises(**kw):
    """Assert some code raises an error.
    Can pass in a message (`check_raises(message="Custom message")`).
    Can pass in an exception (`check_raises(exception=ArgumentError)`).
    """
    message = kw.get('message', "Expected to raise, did not.")
    expected_exception = kw.get('exception', Exception)
    failed = False
    try:
        yield
    except expected_exception:
        failed = True
    except Exception as e:
        message = f"Expected to raise {expected_exception}. Instead received {e.__class__.__name__}"
    finally:
        if not failed:
            assert False, message

def check_is_near(a, b, message=None, **kw):
    """Wrap the numpy isclose function."""
    if message is None:
        message = f"Expected {a} to be close to {b}."
    result = np.isclose(a, b, **kw)
    if np.size(result) == 1: result = [result]
    if not all(result):
        assert False, message

def check_equals(a, b, **kw):
    """Check if two values are equal.
    Not type sensitive.
    Can handle 1 or n-dimensional objects."""
    kw = {**kw, **{'atol': 0, 'message': f"Expected {a} to equal {b}."}}
    return check_is_near(a, b, **kw)

def save_config_file(file, d):
    config = ConfigParser()
    config['DEFAULT'] = d
    config.write(open(file, 'w'))

def read_config_file(file):
    config = ConfigParser()
    config.read(file)
    return config

@lru_cache(maxsize=128)
class Config:
    "Store the basic information for nbdev to work"
    def __init__(self, cfg_name='settings.ini'):
        cfg_path = Path.cwd()
        while cfg_path != Path('/') and not (cfg_path/cfg_name).exists(): cfg_path = cfg_path.parent
        self.config_file = cfg_path/cfg_name
        assert self.config_file.exists(), "Use `Config.create` to create a `Config` object the first time"
        self.d = read_config_file(self.config_file)['DEFAULT']

    def __getattr__(self,k):
        if k=='d' or k not in self.d: raise AttributeError(k)
        return self.config_file.parent/self.d[k] if k.endswith('_path') else self.d[k]

    def get(self,k,default=None):   return self.d.get(k, default)
    def __setitem__(self,k,v): self.d[k] = str(v)
    def __contains__(self,k):  return k in self.d
    def save(self): save_config_file(self.config_file,self.d)

# NOTE: Changed this to hardcode the github--not sure which one is best.
def create_config(lib_name, user, path='.', cfg_name='settings.ini', branch='master',
               git_url="https://github.com/%(user)s/data_lab/tree/%(branch)s/", custom_sidebar=False,
               nbs_path='nbs', lib_path='%(lib_name)s', doc_path='docs', tst_flags='', version='0.0.1'):
    g = locals()
    config = {o:g[o] for o in 'lib_name user branch git_url lib_path nbs_path doc_path tst_flags version custom_sidebar'.split()}
    save_config_file(Path(path)/cfg_name, config)


