import uuid

from django.db import models


class TimeStampedModel(models.Model):
    """
    Clase base abstracta que provee campos UUID y timestamps automáticos.
    Todos los modelos del CRM heredan de esta clase.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']
