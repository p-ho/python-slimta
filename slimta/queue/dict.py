# Copyright (c) 2012 Ian C. Good
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

"""Package implementing the :mod:`slimta.queue` system on top of a
:func:`dict()` backend. This backend can be implemented as a :mod:`shelve` to
provide basic persistence.

"""

import uuid

import gevent
from gevent import Greenlet
from gevent.pool import Pool

from slimta.queue import *

__all__ = ['DictStorage']


class DictStorage(QueueStorage):
    """Stores |Envelope| and queue metadata in two basic dictionary objects.

    :param envelope_db: The dictionary object to hold |Envelope| objects, keyed
                        by a unique string. Defaults to an empty :func:`dict`.
    :param meta_db: The dictionary object to hold envelope metadata, keyed by
                    the same string as ``envelope_db``. Defaults to an empty
                    :func:`dict`.

    """

    def __init__(self, envelope_db, meta_db):
        super(DictStorage, self).__init__()
        self.env_db = envelope_db
        self.meta_db = meta_db

    def write(self, envelope, timestamp):
        while True:
            id = uuid.uuid4().hex
            if not self.env_db.has_key(id):
                self.env_db[id] = envelope
                self.meta_db[id] = (timestamp, 0)
                return id

    def set_timestamp(self, id, timestamp):
        meta = self.meta_db[id]
        self.meta_db[id] = (timestamp, meta[1])

    def increment_attempts(self, id):
        meta = self.meta_db[id]
        new = meta[1] + 1
        self.meta_db[id] = (meta[0], new)
        return new

    def load(self):
        for key in self.meta_db.keys():
            meta = self.meta_db[key]
            yield (meta[0], key)

    def get(self, id):
        return self.env_db[id]

    def remove(self, id):
        try:
            del self.meta_db[id]
        except KeyError:
            pass
        try:
            del self.env_db[id]
        except KeyError:
            pass


# vim:et:fdm=marker:sts=4:sw=4:ts=4
