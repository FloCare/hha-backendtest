from django.db import models
from flocarebase.middleware import get_current_request
import logging
from flocarebase.constants import ANON_USER

logger = logging.getLogger(__name__)


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.CharField(max_length=50, null=True)
    updated_by = models.CharField(max_length=50, null=True)

    class Meta:
        abstract = True

    def is_new_record(self):
        return not self.created_at

    def save(self, *args, **kwargs):
        current_request = get_current_request()
        if current_request:
            try:
                current_user = current_request.user
                if current_user:
                    if self.is_new_record():
                        self.created_by = str(current_user.username)
                    self.updated_by = current_user.username
            except AttributeError:
                logger.error('No User attribute in request object : %s', current_request)
                if self.is_new_record():
                    self.created_by = ANON_USER
                self.updated_by = ANON_USER
        else:
            if self.is_new_record():
                self.created_by = ANON_USER
            self.updated_by = ANON_USER

        super(BaseModel, self).save(*args, **kwargs)
