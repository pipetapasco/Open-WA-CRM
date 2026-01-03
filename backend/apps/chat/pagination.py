from rest_framework.pagination import PageNumberPagination


class MessagePagination(PageNumberPagination):
    """
    Paginación para mensajes de chat.
    Diseñada para Infinite Scroll en el frontend.
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100
