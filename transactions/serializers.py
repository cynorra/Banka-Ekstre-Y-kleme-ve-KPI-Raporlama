from rest_framework import serializers
from .models import Transaction

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ('user', 'unique_hash', 'created_at')

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()