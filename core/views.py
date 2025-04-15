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
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.decorators import throttle_classes
from decimal import Decimal
class SignUpView(APIView):
    """
    User registration endpoint.
    """
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "message": "User registered successfully",
                    "username": user.username,
                    "balance": float(user.balance)
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@throttle_classes([UserRateThrottle])
class LoginView(APIView):
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
                timestamp = timezone.now() - timedelta(days=random.randint(0, 30))
                
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
                    # If any transaction fails, the entire operation will roll back
                    return Response(
                        {'error': f'Transaction creation failed: {str(e)}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Save the final balance after all transactions
            user.save()
        
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'username': user.username,
            'balance': float(user.balance)
        }, status=status.HTTP_200_OK)
    
@throttle_classes([UserRateThrottle])
class UserBalanceView(APIView):
    """
    Authenticated view that returns the current user's balance
    """
    permission_classes = [IsAuthenticated]
    def get(self,request):
        return Response({'balance':request.user.balance})



class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

@throttle_classes([UserRateThrottle])
class UserTransactionsView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get(self, request):
        transactions = Transaction.objects.filter(user=request.user).order_by('-timestamp')
        
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(transactions, request)
        
        serializer = TransactionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
from .serializers import TransactionCreateSerializer

@throttle_classes([UserRateThrottle])
class CreateTransactionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = TransactionCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                # Lock the user's row for update
                user = User.objects.select_for_update().get(pk=request.user.pk)
                
                # Create the transaction
                transaction_obj = serializer.save(user=user)
                
                # Update user balance
                if transaction_obj.transaction_type == Transaction.DEPOSIT:
                    user.balance += transaction_obj.amount
                else:  # Withdrawal
                    user.balance -= transaction_obj.amount
                user.save()
                
                return Response({
                    'message': 'Transaction created successfully',
                    'transaction_id': transaction_obj.id,
                    'amount': float(transaction_obj.amount),
                    'type': transaction_obj.get_transaction_type_display(),
                    'new_balance': float(user.balance),
                    'timestamp': transaction_obj.timestamp
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )