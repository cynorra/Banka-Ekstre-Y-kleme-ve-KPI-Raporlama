from django.urls import path 
from .views import UploadTransactionView, KPIReportView, TransactionListView

urlpatterns = [
    path('list/', TransactionListView.as_view(), name='transaction-list'),
    path('upload/', UploadTransactionView.as_view(), name='transaction-upload'),
    path('reports/summary/', KPIReportView.as_view(), name='kpi-summary'),
]