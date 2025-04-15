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
from django.shortcuts import get_object_or_404
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
    
class LoginView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'
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
            'user_id': user.id,
            'username': user.username,
            'balance': float(user.balance)
        }, status=status.HTTP_200_OK)
    

class UserBalanceView(APIView):
    throttle_classes = [ScopedRateThrottle,UserRateThrottle]
    throttle_scope = 'balance'
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


class UserTransactionsView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    throttle_classes = [ScopedRateThrottle,UserRateThrottle]
    throttle_scope = 'transaction'
    
    def get(self, request):
        transactions = Transaction.objects.filter(user=request.user).order_by('-timestamp')
        
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(transactions, request)
        
        serializer = TransactionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
from .serializers import TransferSerializer

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
    
    def post(self, request):
        serializer = TransferSerializer(data=request.data,context={'request': request})
        serializer.is_valid(raise_exception=True)

        recipient_id = serializer.validated_data['recipient_id']
        amount = serializer.validated_data['amount']
        description = serializer.validated_data.get('description', '')

        try:
            with transaction.atomic():
                # Lock both user rows to prevent concurrent modifications
                sender = User.objects.select_for_update().get(pk=request.user.pk)
                recipient = get_object_or_404(User.objects.select_for_update(), pk=recipient_id)

                # Validate sufficient balance
                if sender.balance < amount:
                    return Response(
                        {'error': 'Insufficient funds'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Create transactions
                Transaction.objects.create(
                    user=sender,
                    amount=amount,
                    transaction_type=Transaction.WITHDRAWAL,
                    description=f"Transfer to {recipient.username}: {description}"
                )
                Transaction.objects.create(
                    user=recipient,
                    amount=amount,
                    transaction_type=Transaction.DEPOSIT,
                    description=f"Transfer from {sender.username}: {description}"
                )

                # Update balances
                sender.balance -= amount
                recipient.balance += amount
                sender.save()
                recipient.save()

                return Response({
                    'message': 'Transfer successful',
                    'new_balance': float(sender.balance),
                    'transaction_id': Transaction.objects.latest('id').id
                }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': f'Transfer failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )