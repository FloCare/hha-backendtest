from django.db import models
from user_auth.middleware import get_current_request


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
            current_user = current_request.user
            if current_user and self.is_new_record():
                self.created_by = str(current_user.username)
            self.updated_by = current_user.username

        super(BaseModel, self).save(*args, **kwargs)