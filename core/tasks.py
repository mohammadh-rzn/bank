# tasks.py
from background_task import background
from django.db import transaction
from decimal import Decimal
import random
from .models import Transaction, User
from django.utils import timezone
from .cache_utils import *
from .logging import log_api_event

@background
def process_login_transactions(user_id):
    try:
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=user_id)
            num_transactions = random.randint(1, 10)
            created_transactions = []
            
            for _ in range(num_transactions):
                is_deposit = random.choice([True, False])
                amount = round(Decimal(random.uniform(1.00, 1000.00)), 2)
                timestamp = timezone.now()
                
                if is_deposit:
                    t = Transaction.objects.create(
                        user=user,
                        amount=amount,
                        transaction_type=Transaction.DEPOSIT,
                        timestamp=timestamp,
                        description=f"Random deposit #{_ + 1}"
                    )
                    user.balance += amount
                else:
                    if user.balance >= amount:
                        t = Transaction.objects.create(
                            user=user,
                            amount=amount,
                            transaction_type=Transaction.WITHDRAWAL,
                            timestamp=timestamp,
                            description=f"Random withdrawal #{_ + 1}"
                        )
                        user.balance -= amount
                    else:
                        continue
                
                created_transactions.append({
                    'id': t.id,
                    'amount': float(t.amount),
                    'type': t.get_transaction_type_display(),
                    'timestamp': t.timestamp.isoformat(),
                    'new_balance': float(user.balance)
                })
            
            user.save()
            invalidate_user_caches(user.id)
            return {
                'status': 'success',
                'user_id': user.id,
                'transactions': created_transactions
            }
            
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'user_id': user_id
        }

# tasks.py
def handle_login_transactions_result(task):
    if task.success:
        result = task.result
        if result['status'] == 'success':
            log_api_event(
                "login_transactions_completed",
                user_id=result['user_id'],
                transaction_count=len(result['transactions']),
                status="success"
            )
        else:
            log_api_event(
                "login_transactions_failed",
                user_id=result['user_id'],
                error=result['error'],
                status="failed"
            )