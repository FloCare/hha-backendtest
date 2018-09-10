from threading import local
from django.db import connection
from time import time
from operator import add
import functools
import logging
from django.conf import settings

logger = logging.getLogger(__name__)
_thread_locals = local()


def get_current_request():
    return getattr(_thread_locals, 'request', None)


class UserInformationMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        response = self.get_response(request)
        return response


class DBStatsMiddleWare(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # TODO Should add something to disable it in production if needed
        if not settings.DEBUG:
            return None

        # get number of db queries before we do anything
        n = len(connection.queries)

        # time the view
        start = time()
        response = view_func(request, *view_args, **view_kwargs)
        total_time = time() - start

        # compute the db time for the queries just run
        db_queries = len(connection.queries) - n
        if db_queries:
            db_time = functools.reduce(add, [float(q['time']) for q in connection.queries[n:]])
        else:
            db_time = 0.0

        # and backout python time
        python_time = total_time - db_time

        stats = {
            'total_time': str(round(total_time, 7)),
            'python_time': str(round(python_time, 7)) + ' ' + str(round(100.0*python_time/total_time, 1)) + '%',
            'db_time': str(round(db_time, 7)) + ' ' + str(round(100.0*db_time/total_time, 1)) + '%',
            'db_queries': db_queries,
        }

        logger.debug('stats')
        logger.debug(stats)

        return response
