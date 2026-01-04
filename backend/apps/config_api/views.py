from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.chat.tasks import process_webhook_payload

from .models import WhatsAppAccount, WhatsAppTemplate
from .serializers import WhatsAppAccountSerializer, WhatsAppTemplateSerializer


class WhatsAppAccountViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar cuentas de WhatsApp Business.
    """

    serializer_class = WhatsAppAccountSerializer

    def get_queryset(self):
        return WhatsAppAccount.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def sync_templates(self, request, pk=None):
        import httpx

        account = self.get_object()

        if not account.business_account_id or not account.access_token:
            return Response(
                {
                    'status': 'error',
                    'message': 'Account is missing business_account_id or access_token',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        api_url = f'https://graph.facebook.com/v18.0/{account.business_account_id}/message_templates'
        headers = {
            'Authorization': f'Bearer {account.access_token}',
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(api_url, headers=headers)

            if response.status_code != 200:
                return Response(
                    {
                        'status': 'error',
                        'message': f'Meta API error: {response.status_code}',
                        'details': response.text,
                    },
                    status=status.HTTP_502_BAD_GATEWAY,
                )

            data = response.json()
            templates_data = data.get('data', [])

            synced_count = 0
            updated_count = 0

            for tmpl in templates_data:
                template, created = WhatsAppTemplate.objects.update_or_create(
                    account=account,
                    name=tmpl.get('name'),
                    language=tmpl.get('language'),
                    defaults={
                        'category': tmpl.get('category', 'UTILITY'),
                        'status': tmpl.get('status', 'PENDING'),
                        'components': tmpl.get('components', []),
                    },
                )
                if created:
                    synced_count += 1
                else:
                    updated_count += 1

            return Response(
                {
                    'status': 'success',
                    'message': f'Synced {synced_count} new templates, updated {updated_count}',
                    'total_from_meta': len(templates_data),
                    'synced': synced_count,
                    'updated': updated_count,
                },
                status=status.HTTP_200_OK,
            )

        except httpx.RequestError as e:
            return Response(
                {
                    'status': 'error',
                    'message': f'Failed to connect to Meta API: {str(e)}',
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception as e:
            return Response(
                {
                    'status': 'error',
                    'message': f'Unexpected error: {str(e)}',
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class WhatsAppTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar plantillas de WhatsApp.
    """

    serializer_class = WhatsAppTemplateSerializer
    filterset_fields = ['account', 'category', 'status', 'language']

    def get_queryset(self):
        user_accounts = self.request.user.whatsapp_accounts.all()
        return WhatsAppTemplate.objects.filter(account__in=user_accounts).select_related('account')


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def webhook(request, phone_number_id):
    account = WhatsAppAccount.objects.filter(phone_number_id=phone_number_id).first()

    if not account:
        return HttpResponse('Not Found', status=404)

    if request.method == 'GET':
        mode = request.query_params.get('hub.mode')
        token = request.query_params.get('hub.verify_token')
        challenge = request.query_params.get('hub.challenge')

        if mode == 'subscribe' and token:
            if account.webhook_verify_token == token:
                return HttpResponse(challenge, content_type='text/plain', status=200)
            else:
                return HttpResponse('Forbidden', status=403)

        return HttpResponse('Bad Request', status=400)

    elif request.method == 'POST':
        payload = request.data

        process_webhook_payload.delay(payload, phone_number_id)

        return Response({'status': 'ok'}, status=200)
