from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from .models import Contact
from .serializers import ContactSerializer


class ContactViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Contactos.
    """

    serializer_class = ContactSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['name', 'phone_number']
    filterset_fields = ['account']

    def get_queryset(self):
        user_accounts = self.request.user.whatsapp_accounts.all()
        return (
            Contact.objects.filter(account__in=user_accounts)
            .select_related('account')
            .annotate(conversations_count=Count('conversations'))
            .order_by('-created_at')
        )

    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        contact_ids = request.data.get('ids', [])
        if not contact_ids:
            return Response({'error': 'No se proporcionaron IDs de contactos.'}, status=status.HTTP_400_BAD_REQUEST)

        deleted_count, _ = Contact.objects.filter(
            id__in=contact_ids,
            account__in=request.user.whatsapp_accounts.all()
            if not request.user.is_superuser
            else Contact.objects.all().values('account'),
        ).delete()

        return Response({'deleted': deleted_count})

    @action(detail=False, methods=['post'])
    def bulk_send_template(self, request):
        from apps.chat.serializers import SendTemplateMessageSerializer
        from apps.chat.services import (
            TemplateData,
            WhatsAppNotificationService,
        )

        contact_ids: list[str] = request.data.get('ids', [])
        template_data_raw: dict = request.data.get('template_data', {})

        if not contact_ids:
            return Response({'error': 'No se proporcionaron IDs de contactos.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = SendTemplateMessageSerializer(data=template_data_raw)
        serializer.is_valid(raise_exception=True)

        template_data = TemplateData.from_validated_data(serializer.validated_data)

        contacts = Contact.objects.select_related('account').filter(id__in=contact_ids)

        service = WhatsAppNotificationService()
        results: dict[str, int | list[str]] = {'success': 0, 'failed': 0, 'errors': []}

        for contact in contacts:
            result = service.send_template_to_contact(
                contact=contact, account=contact.account, template_data=template_data
            )

            if result.success:
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append(f'Error con contacto {contact.id}: {result.error}')

        return Response(results)
