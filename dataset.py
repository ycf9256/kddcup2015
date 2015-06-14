#! /usr/local/bin/python3
# -*- utf-8 -*-


"""
Generate datasets for training and validating, and load dataset of testing.
"""


import numpy as np
from datetime import datetime, timedelta
import logging
import sys
import os

import config
import util

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
                    format='%(asctime)s %(name)s %(levelname)s\t%(message)s')


def load_test():
    """
    Load dataset for testing.

    Returns
    -------
    X: numpy ndarray, shape: (num_of_enrollments, num_of_features)
    Rows of features.
    """
    pkl_path = util.cache_path('test_X')
    if os.path.exists(pkl_path):
        X = util.fetch(pkl_path)
    else:
        enroll_set = np.sort(util.load_enrollment_test()['enrollment_id'])
        # log = util.load_logs()
        # base_date = log['time'].max().to_datetime()
        base_date = datetime(2014, 8, 1, 22, 0, 47)
        X = None
        for f in config.MODELING['features']:
            X_ = f(enroll_set, base_date)
            if X is None:
                X = X_
            else:
                X = np.c_[X, X_]
        util.dump(X, pkl_path)
    return X


def __enroll_ids_with_log__(enroll_ids, log, base_date):
    log_eids = set(log[log['time'] <= base_date]['enrollment_id'].unique())
    return np.array([eid for eid in enroll_ids if eid in log_eids])


def __load_dataset__(enroll_ids, log, base_date):
    # get all instances in this time span
    X = None
    for f in config.MODELING['features']:
        X_ = f(enroll_ids, base_date)
        if X is None:
            X = X_
        else:
            X = np.c_[X, X_]

    # get labels in this time span
    active_eids = set(log[log['time'] > base_date]['enrollment_id']
                      .unique())
    y = [int(eid not in active_eids) for eid in enroll_ids]

    return X, y


def load_train():
    """
    Load dataset for training and validating.

    *NOTE*  If you need a validating set, you SHOULD split from training set
    by yourself.

    Returns
    -------
    X: numpy ndarray, shape: (num_of_enrollments, num_of_features)
    Rows of features.

    y: numpy ndarray, shape: (num_of_enrollments,)
    Vector of labels.
    """
    logger = logging.getLogger('load_train')
    enroll_ids = np.sort(util.load_enrollment_train()['enrollment_id'])
    log = util.load_logs()[['enrollment_id', 'time']]
    # base_date = log['time'].max().to_datetime() - timedelta(days=10)
    base_date = datetime(2014, 7, 22, 22, 0, 47)
    if util is not None and util < base_date:
        base_date = util
    Dw = timedelta(days=7)
    X = None
    y = []
    enroll_ids = __enroll_ids_with_log__(enroll_ids, log, base_date)
    while enroll_ids.size > 0:
        logger.debug('load features before %s', base_date)

        # get instances and labels
        X_temp, y_temp = __load_dataset__(enroll_ids, log, base_date)

        # update instances and labels
        if X is None:
            X = X_temp
        else:
            X = np.r_[X, X_temp]

        y += y_temp

        # update log, base_date and enroll_ids
        log = log[log['time'] <= base_date]
        base_date -= Dw
        enroll_ids = __enroll_ids_with_log__(enroll_ids, log, base_date)

    return X, np.array(y, dtype=np.int)
