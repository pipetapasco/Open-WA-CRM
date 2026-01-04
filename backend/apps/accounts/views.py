from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from .serializers import RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    """
    Endpoint para registro de nuevos usuarios.
    
    POST /api/auth/register/
    Body: {
        "username": "usuario",
        "email": "correo@ejemplo.com",
        "password": "contraseña123",
        "password_confirm": "contraseña123",
        "first_name": "Nombre",  # opcional
        "last_name": "Apellido"   # opcional
    }
    """
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response({
            'status': 'success',
            'message': 'Usuario registrado exitosamente.',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            }
        }, status=status.HTTP_201_CREATED)


class MeView(APIView):
    """
    Endpoint para obtener información del usuario actual.
    
    GET /api/auth/me/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
