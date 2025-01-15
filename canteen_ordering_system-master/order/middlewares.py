# order/middlewares.py

from django.contrib.sessions.middleware import SessionMiddleware

class SeparateSessionMiddleware(SessionMiddleware):
    def process_request(self, request):
        # Separate sessions for admin and users
        request.session = self.SessionStore()
        super().process_request(request)
