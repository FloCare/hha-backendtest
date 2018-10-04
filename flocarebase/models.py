from django.db import models
from flocarebase.middleware import get_current_request
import logging
from flocarebase.constants import ANON_USER

logger = logging.getLogger(__name__)


def get_current_user():
    current_request = get_current_request()
    try:
        if current_request:
            return current_request.user
        return None
    except AttributeError:
        logger.error('No User attribute in request object : %s', current_request)
        return None


class BaseModelManager(models.Manager):
    def bulk_create(self, objects, batch_size=None):
        current_user = get_current_user()
        for object in objects:
            object.created_by = getattr(current_user, 'username', ANON_USER)
            object.updated_by = getattr(current_user, 'username', ANON_USER)
        return super(BaseModelManager, self).bulk_create(objects, batch_size)


class BaseModel(models.Model):

    objects = BaseModelManager()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.CharField(max_length=50, null=True)
    updated_by = models.CharField(max_length=50, null=True)

    class Meta:
        abstract = True

    def is_new_record(self):
        return not self.created_at

    def save(self, *args, **kwargs):
        current_user = get_current_user()
        if self.is_new_record():
            self.created_by = getattr(current_user, 'username', ANON_USER)
        self.updated_by = getattr(current_user, 'username', ANON_USER)

        super(BaseModel, self).save(*args, **kwargs)
