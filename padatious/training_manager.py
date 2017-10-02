# Copyright 2017 Mycroft AI, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import multiprocessing as mp
from os import mkdir
from os.path import join, isfile, isdir, splitext

import padatious
from padatious.train_data import TrainData
from padatious.util import lines_hash


def _train_and_save(obj, cache, data, print_updates):
    """Internal pickleable function used to train objects in another process"""
    obj.train(data)
    if print_updates:
        print('Regenerated ' + obj.name + '.')
    obj.save(cache)


class TrainingManager(object):
    """
    Manages multithreaded training of either Intents or Entities

    Args:
        cls (Type[Trainable]): Class to wrap
        cache_dir (str): Place to store cache files
    """
    def __init__(self, cls, cache_dir):
        self.cls = cls
        self.cache = cache_dir
        self.objects = []
        self.objects_to_train = []

        self.train_data = TrainData()

    def add(self, name, lines, reload_cache=False):
        hash_fn = join(self.cache, name + '.hash')
        old_hsh = None
        if isfile(hash_fn):
            with open(hash_fn, 'rb') as g:
                old_hsh = g.read()
        min_ver = splitext(padatious.__version__)[0]
        new_hsh = lines_hash([min_ver] + lines)
        if reload_cache or old_hsh != new_hsh:
            self.objects_to_train.append(self.cls(name=name, hsh=new_hsh))
        else:
            self.objects.append(self.cls.from_file(name=name, folder=self.cache))
        self.train_data.add_lines(name, lines)

    def load(self, name, file_name, reload_cache=False):
        with open(file_name) as f:
            self.add(name, f.readlines(), reload_cache)

    def train(self, debug=True, single_thread=False):
        if not isdir(self.cache):
            mkdir(self.cache)

        def args(i):
            return i, self.cache, self.train_data, debug

        if single_thread:
            for i in self.objects_to_train:
                _train_and_save(*args(i))
        else:
            # Train in multiple processes to disk
            pool = mp.Pool()
            try:
                results = [
                    pool.apply_async(_train_and_save, args(i))
                    for i in self.objects_to_train
                ]

                for i in results:
                    i.get()
            finally:
                pool.close()

        # Load saved objects from disk
        for obj in self.objects_to_train:
            self.objects.append(self.cls.from_file(name=obj.name, folder=self.cache))
