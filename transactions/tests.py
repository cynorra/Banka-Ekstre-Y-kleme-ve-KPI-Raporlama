from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from decimal import Decimal
from .models import Transaction
from django.core.files.uploadedfile import SimpleUploadedFile

class TransactionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_upload_csv(self):
        csv_content = (
            b"date,amount,currency,description,type\n"
            b"2025-07-01,1000.00,TRY,Test Gelir,credit\n"
            b"2025-07-02,-500.00,TRY,Test Gider,debit"
        )
        file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")
        
        response = self.client.post('/api/transactions/upload/', {'file': file}, format='multipart')
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Transaction.objects.count(), 2)
        
        # Kategori kontrolü (Auto-categorize 'Diğer İşlemler' dönecek çünkü keyword yok)
        self.assertEqual(Transaction.objects.first().category, 'Diğer İşlemler')

    def test_kpi_report(self):
        Transaction.objects.create(
            user=self.user, date='2025-07-01', amount=2000, 
            description='Gelir', transaction_type='credit', unique_hash='hash1'
        )
        Transaction.objects.create(
            user=self.user, date='2025-07-02', amount=-500, 
            description='Gider', transaction_type='debit', unique_hash='hash2'
        )
        
        response = self.client.get('/api/transactions/reports/summary/?start_date=2025-07-01&end_date=2025-07-31')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['net_cash_flow'], 1500)