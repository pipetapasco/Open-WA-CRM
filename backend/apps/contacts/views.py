from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count

from .models import Contact
from .serializers import ContactSerializer


class ContactViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Contactos.
    
    Endpoints:
    - GET /contacts/ - Listar contactos
    - POST /contacts/ - Crear contacto
    - GET /contacts/{id}/ - Detalle
    - PUT/PATCH /contacts/{id}/ - Actualizar
    - DELETE /contacts/{id}/ - Eliminar
    
    Filtros:
    - ?account={uuid} - Filtrar por cuenta de WhatsApp
    - ?search={term} - Buscar por nombre o teléfono
    """
    serializer_class = ContactSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['name', 'phone_number']
    filterset_fields = ['account']

    def get_queryset(self):
        """
        Retorna contactos ordenados por creación reciente,
        anotados con el conteo de conversaciones.
        """
        return Contact.objects.select_related('account').annotate(
            conversations_count=Count('conversations')
        ).order_by('-created_at')
