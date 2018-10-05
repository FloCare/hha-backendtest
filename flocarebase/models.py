from django.db import models
from flocarebase.middleware import get_current_request
import logging
from flocarebase.constants import ANON_USER
from django.utils import timezone

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


class BaseQuerySet(models.QuerySet):
    def soft_delete(self):
        return super(BaseQuerySet, self).update(deleted_at=timezone.now())


class BaseModelManager(models.Manager):
    def bulk_create(self, objects, batch_size=None):
        current_user = get_current_user()
        for object in objects:
            object.created_by = getattr(current_user, 'username', ANON_USER)
            object.updated_by = getattr(current_user, 'username', ANON_USER)
        return super(BaseModelManager, self).bulk_create(objects, batch_size)

    def get_queryset(self):
        return BaseQuerySet(self.model).filter(deleted_at=None)
        # return super().get_queryset().filter(deleted_at=None)


class AllObjectsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()


class BaseModel(models.Model):

    objects = BaseModelManager()
    all_objects = AllObjectsManager()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, default=None)

    created_by = models.CharField(max_length=50, null=True)
    updated_by = models.CharField(max_length=50, null=True)

    class Meta:
        abstract = True

    def is_deleted(self):
        return not not self.deleted_at

    def is_active(self):
        return not self.deleted_at

    def is_new_record(self):
        return not self.created_at

    def save(self, *args, **kwargs):
        current_user = get_current_user()
        if self.is_new_record():
            self.created_by = getattr(current_user, 'username', ANON_USER)
        self.updated_by = getattr(current_user, 'username', ANON_USER)

        super(BaseModel, self).save(*args, **kwargs)

    def soft_delete(self):
        self.deleted_at = timezone.now()
        return self.save()
