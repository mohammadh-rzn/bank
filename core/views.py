from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import LoginSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from .models import Transaction, User
from .serializers import TransactionSerializer
import random
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from rest_framework.throttling import UserRateThrottle,ScopedRateThrottle
from rest_framework.decorators import throttle_classes
from decimal import Decimal
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from .logging import log_api_event

from opentelemetry import trace

tracer = trace.get_tracer(__name__)
class SignUpView(APIView):
    """
    User registration endpoint.
    """
    @swagger_auto_schema(
        operation_description="Signup new user",
        request_body=UserSerializer
    )
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            log_api_event(
                "user_registered",
                username=user.username,
                user_id=user.id,
                status="success",
                client_ip=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
            )
            return Response(
                {
                    "message": "User registered successfully",
                    "username": user.username,
                    "balance": float(user.balance)
                },
                status=status.HTTP_201_CREATED
            )
        log_api_event(
            "user_registration_failed",
            errors=serializer.errors,
            status="failed",
            client_ip=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def signup_view(request):
    """Render the initial signup page"""
    return render(request, 'signup.html')
    
class LoginView(APIView):
    """
    login user and generate 1-10 random transactions upon login
    """
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'
    @swagger_auto_schema(
        operation_description="User login",
        request_body=LoginSerializer,
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        num_transactions = random.randint(1, 10)
        created_transactions = []
        
        with transaction.atomic():
            # Lock the user's row for the entire operation
            user = User.objects.select_for_update().get(pk=user.pk)
            
            for _ in range(num_transactions):
                # Generate random transaction data
                is_deposit = random.choice([True, False])
                amount = round(random.uniform(1.00, 1000.00), 2)
                timestamp = timezone.now()
                
                try:
                    if is_deposit:
                        # Create deposit
                        t = Transaction.objects.create(
                            user=user,
                            amount=amount,
                            transaction_type=Transaction.DEPOSIT,
                            timestamp=timestamp,
                            description=f"Random deposit #{_ + 1}"
                        )
                        user.balance += Decimal(amount)
                    else:
                        # Create withdrawal (only if sufficient funds)
                        if user.balance >= amount:
                            t = Transaction.objects.create(
                                user=user,
                                amount=amount,
                                transaction_type=Transaction.WITHDRAWAL,
                                timestamp=timestamp,
                                description=f"Random withdrawal #{_ + 1}"
                            )
                            user.balance -= Decimal(amount)
                        else:
                            continue  # Skip this withdrawal if insufficient funds
                    
                    created_transactions.append({
                        'id': t.id,
                        'amount': float(t.amount),
                        'type': t.get_transaction_type_display(),
                        'timestamp': t.timestamp,
                        'new_balance': float(user.balance)
                    })
                    
                except Exception as e:
                    log_api_event(
                            "login_transaction_failed",
                            user_id=user.id,
                            username=user.username,
                            error=str(e),
                            status="failed",
                            transaction_count=len(created_transactions),
                            client_ip=request.META.get('REMOTE_ADDR'),
                    )
                    # If any transaction fails, the entire operation will roll back
                    return Response(
                        {'error': f'Transaction creation failed: {str(e)}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Save the final balance after all transactions
            user.save()
        
        
        refresh = RefreshToken.for_user(user)
        log_api_event(
                "user_login",
                user_id=user.id,
                username=user.username,
                status="success",
                transaction_count=len(created_transactions),
                final_balance=float(user.balance),
                client_ip=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
        )
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user_id': user.id,
            'username': user.username,
            'balance': float(user.balance)
        }, status=status.HTTP_200_OK)
    
def login_view(request):
    """Render the login template"""
    return render(request, 'login.html')
class UserBalanceView(APIView):
    throttle_classes = [ScopedRateThrottle,UserRateThrottle]
    throttle_scope = 'balance'
    """
    Authenticated view that returns the current user's balance
    """
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Get current user balance",
        security=[{"Bearer": []}]
    )
    def get(self,request):
        return Response({'balance':request.user.balance})



class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class UserTransactionsView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    throttle_classes = [ScopedRateThrottle,UserRateThrottle]
    throttle_scope = 'transaction'
    @swagger_auto_schema(
        operation_description="Get a paginated list of transactions",
        
        security=[{"Bearer": []}]
    )
    def get(self, request):
        transactions = Transaction.objects.filter(user=request.user).order_by('-timestamp')
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(transactions, request)
        
        serializer = TransactionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
from .serializers import TransferSerializer

from opentelemetry import metrics

meter = metrics.get_meter(__name__)

# Define metrics
transfer_counter = meter.create_counter(
    "banking.transfers.count",
    description="Count of transfer operations",
    unit="1",
)

transfer_amount = meter.create_histogram(
    "banking.transfers.amount",
    description="Distribution of transfer amounts",
    unit="USD",
)
class TransferView(APIView):
    """
    Transfer funds between authenticated user and another user by ID
    Requires:
    - recipient_id: ID of recipient user
    - amount: Positive decimal value
    - description: Optional transaction memo
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle,UserRateThrottle]
    throttle_scope = 'transfer'
    @swagger_auto_schema(
        operation_description="Get a paginated list of transactions",
        request_body=TransferSerializer,
        security=[{"Bearer": []}]
    )
    def post(self, request):
        with tracer.start_as_current_span("TransferView.post") as span:
            serializer = TransferSerializer(data=request.data,context={'request': request})
            serializer.is_valid(raise_exception=True)

            recipient_id = serializer.validated_data['recipient_id']
            amount = serializer.validated_data['amount']
            description = serializer.validated_data.get('description', '')
            span.set_attributes({
                "user.id": request.user.id,
                "transfer.amount": float(amount),
                "transfer.recipient": recipient_id,
            })
            try:
                with tracer.start_as_current_span("transfer_transaction"), transaction.atomic():
                    # Lock both user rows to prevent concurrent modifications
                    sender = User.objects.select_for_update().get(pk=request.user.pk)
                    recipient = get_object_or_404(User.objects.select_for_update(), pk=recipient_id)

                    # Validate sufficient balance
                    if sender.balance < amount:
                        span.set_attribute("transfer.status", "failed")
                        span.set_attribute("transfer.failure_reason", "insufficient_funds")
                        return Response(
                            {'error': 'Insufficient funds'},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # Create transactions
                    with tracer.start_as_current_span("create_withdrawal"):
                        Transaction.objects.create(
                            user=sender,
                            amount=amount,
                            transaction_type=Transaction.WITHDRAWAL,
                            description=f"Transfer to {recipient.username}: {description}"
                        )
                    with tracer.start_as_current_span("create_deposit"):    
                        Transaction.objects.create(
                            user=recipient,
                            amount=amount,
                            transaction_type=Transaction.DEPOSIT,
                            description=f"Transfer from {sender.username}: {description}"
                        )

                    # Update balances
                    with tracer.start_as_current_span("update_balances"):
                        sender.balance -= amount
                        recipient.balance += amount
                        sender.save()
                        recipient.save()
                    span.set_attributes({
                        "transfer.status": "success",
                        "sender.new_balance": float(sender.balance),
                    })
                    transfer_counter.add(1, {
                        "status": "success",
                        "sender": str(request.user.id),
                        "recipient": str(recipient_id),
                    })
                    transfer_amount.record(float(amount), {
                        "sender": str(request.user.id),
                        "recipient": str(recipient_id),
                    })
                    log_api_event(
                        "transfer_completed",
                        sender_id=sender.id,
                        recipient_id=recipient.id,
                        amount=float(amount),
                        new_sender_balance=float(sender.balance),
                        status="success",
                        client_ip=request.META.get('REMOTE_ADDR'),
                    )

                    return Response({
                        'message': 'Transfer successful',
                        'new_balance': float(sender.balance),
                        'transaction_id': Transaction.objects.latest('id').id
                    }, status=status.HTTP_200_OK)

            except Exception as e:
                span.record_exception(e)
                span.set_attributes({
                    "transfer.status": "failed",
                    "transfer.error": str(e),
                })
                transfer_counter.add(1, {
                    "status": "failed",
                    "sender": str(request.user.id),
                    "error": type(e).__name__,
                })
                log_api_event(
                    "transfer_failed",
                    sender_id=request.user.id,
                    recipient_id=recipient_id,
                    amount=float(amount),
                    error=str(e),
                    status="failed",
                    client_ip=request.META.get('REMOTE_ADDR'),
                )
                return Response(
                    {'error': f'Transfer failed: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

def dashboard_view(request):
    """Main dashboard view that renders the template"""
    return render(request, 'dashboard.html')
