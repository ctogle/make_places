import cPickle as pickle
import os

import pdb

def save_pkl(data, filename):
    with open(filename, 'wb') as output: pickle.dump(data, output)

def load_pkl(filename):
    with open(filename, 'rb') as pkl_file: data = pickle.load(pkl_file)
    return data

def file_exists(filename, top_path = None):
    if top_path is None: top_path = os.getcwd()
    return filename in os.listdir(top_path)



