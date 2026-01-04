from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import AIConfig, AIProvider
from .serializers import AIConfigSerializer


class AIConfigViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar configuraciones de IA.
    """

    serializer_class = AIConfigSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['account', 'enabled', 'provider']

    def get_queryset(self):
        return AIConfig.objects.filter(account__owner=self.request.user).select_related('account')

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()

    @action(detail=False, methods=['get'])
    def providers(self, request):
        providers = [{'id': code, 'name': label} for code, label in AIProvider.choices]
        return Response(providers)
