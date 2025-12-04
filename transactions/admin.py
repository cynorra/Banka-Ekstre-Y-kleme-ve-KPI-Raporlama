from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'amount', 'category', 'transaction_type')
    list_filter = ('transaction_type', 'category', 'date')
    search_fields = ('description', 'user_username')