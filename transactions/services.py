import csv
import io
import hashlib
from decimal import Decimal
from datetime import datetime
from .models import Transaction

def auto_categorize(description):
    """
    CSV'deki 'description' alanına göre otomatik kategori belirler.
    """
    desc = description.lower()
    
    if 'fatura #' in desc:
        return 'Satış Gelirleri'
    if 'kira' in desc:
        return 'Kira & Ofis'
    if 'saas' in desc or 'crm' in desc or 'yazılım' in desc:
        return 'Yazılım & Lisans'
    if 'kırtasiye' in desc:
        return 'Ofis Malzemeleri'
    if 'maaş' in desc or 'personel' in desc:
        return 'Personel Giderleri'
    if 'elektrik' in desc or 'su' in desc or 'internet' in desc:
        return 'Faturalar & Altyapı'
    
    return 'Diğer İşlemler'

def process_csv(file, user):
    """
    CSV dosyasını okur, parse eder ve veritabanına kaydetmek üzere nesneleri hazırlar.
    """
    # Dosyayı utf-8-sig ile decode etme burasi onemli (Türkçe karakter ve BOM sorunu olmasın diye)
    decoded_file = file.read().decode('utf-8-sig')
    io_string = io.StringIO(decoded_file)
    
    # CSV Header: date,amount,currency,description,type
    reader = csv.DictReader(io_string)
    
    transactions_to_create = []
    errors = []

    for index, row in enumerate(reader):
        try:
            trans_date = datetime.strptime(row['date'], '%Y-%m-%d').date()
            amount = Decimal(row['amount'])
            description = row['description']
            currency = row['currency']
            t_type = row['type']
            
            transaction = Transaction(
                user=user,
                date=trans_date,
                amount=amount,
                currency=currency,
                description=description,
                transaction_type=t_type,
                category=auto_categorize(description)
            )
            
            # Bulk Create işlemi .save() metodunu tetiklemez.
            # Bu yüzden Hash'i burada manuel hesaplıyoruz.
            raw_string = f"{user.id}{trans_date}{amount}{description}"
            transaction.unique_hash = hashlib.sha256(raw_string.encode('utf-8')).hexdigest()
            
            transactions_to_create.append(transaction)
            
        except KeyError as e:
            errors.append(f"Satır {index+1}: Eksik kolon adı - {e}")
        except ValueError as e:
            errors.append(f"Satır {index+1}: Veri formatı hatası - {e}")
        except Exception as e:
            errors.append(f"Satır {index+1}: Beklenmedik hata - {str(e)}")

    return transactions_to_create, errors