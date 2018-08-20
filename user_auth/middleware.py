from threading import local

_thread_locals = local()


def get_current_request():
    return getattr(_thread_locals, 'request', None)


class UserInformationMiddleware(object):
    def __init__(self, get_response):
        print('init middleware')
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        return None
