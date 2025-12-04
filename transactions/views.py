from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status, parsers
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Sum

from .models import Transaction
from .serializers import TransactionSerializer, FileUploadSerializer
from .services import process_csv

class TransactionListView(ListAPIView):
    """Kullanıcının tüm işlemlerini listeler ve filtreler."""
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Transaction.objects.filter(user=user).order_by('-date')
        
        # Filtreleme (Opsiyonel)
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__icontains=category)
            
        return queryset

class UploadTransactionView(APIView):
    """CSV dosyasını yükler ve atomic işlemle kaydeder."""
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        file_obj = request.FILES['file']
        
        try:
            # Atomic Transaction: Ya hepsi yüklenir ya hiçbiri.
            with transaction.atomic():
                transactions_list, errors = process_csv(file_obj, request.user)
                
                if errors:
                    # CSV içinde hatalı satır varsa işlemi iptal et
                    return Response({
                        "status": "failed", 
                        "message": "CSV dosyasında hatalar var.",
                        "errors": errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Bulk Create: Performans için toplu kayıt.
                # ignore_conflicts=True: Eğer aynı veri (hash) varsa veritabanı hatası vermez, o satırı atlar.
                created_objs = Transaction.objects.bulk_create(transactions_list, ignore_conflicts=True)
                
                return Response({
                    "message": "İşlem başarılı.",
                    "processed_count": len(transactions_list),
                    "inserted_count": len(created_objs) # ignore_conflicts nedeniyle farklı olabilir
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class KPIReportView(APIView):
    """Belirli tarih aralığındaki finansal özeti döner."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not (start_date and end_date):
            return Response({"error": "start_date ve end_date parametreleri zorunludur."}, status=400)

        # Tarih aralığına göre filtreleme
        qs = Transaction.objects.filter(user=request.user, date__range=[start_date, end_date])
        
        # 1. Toplam Gelir
        total_income = qs.filter(transaction_type='credit').aggregate(Sum('amount'))['amount__sum'] or 0
        
        # 2. Toplam Gider (CSV'de negatif geldiği için topluyoruz)
        raw_expense_sum = qs.filter(transaction_type='debit').aggregate(Sum('amount'))['amount__sum'] or 0
        
        # 3. Net Nakit Akışı (Gelir + (-Gider))
        net_cash_flow = total_income + raw_expense_sum
        
        # Gideri raporda pozitif sayı olarak göstermek daha reelistik
        total_expense_abs = abs(raw_expense_sum)

        # 4. En Çok Harcama Yapılan Kategoriler (Top 3)
        # En küçük (en negatif) değerleri bulup sıralıyoruz
        top_categories_qs = (
            qs.filter(transaction_type='debit')
            .values('category')
            .annotate(total=Sum('amount'))
            .order_by('total')[:3]
        )
        
        top_categories_list = [
            {"category": item['category'], "amount": abs(item['total'])}
            for item in top_categories_qs
        ]

        return Response({
            "period": f"{start_date} - {end_date}",
            "summary": {
                "total_income": total_income,
                "total_expense": total_expense_abs,
                "net_cash_flow": net_cash_flow
            },
            "top_expense_categories": top_categories_list
        })