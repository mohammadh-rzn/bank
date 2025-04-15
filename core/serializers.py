from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
User = get_user_model()
from .models import Transaction
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'balance')
        extra_kwargs = {
            'balance': {'required': False}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            balance=validated_data.get('balance', 0.00)
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
from rest_framework import serializers

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(request=self.context.get('request'),
                                username=username,
                                password=password)
            
            if not user:
                msg = 'Unable to log in with provided credentials.'
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = 'Must include "username" and "password".'
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ('id', 'amount', 'transaction_type', 'timestamp', 'description')
        read_only_fields = fields  # All fields are read-only


class TransactionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['amount', 'transaction_type', 'description']
        extra_kwargs = {
            'amount': {'min_value': 0.01},
            'description': {'required': False, 'allow_blank': True}
        }

    def validate(self, data):
        if data['transaction_type'] == Transaction.WITHDRAWAL:
            user = self.context['request'].user
            if user.balance < data['amount']:
                raise serializers.ValidationError(
                    "Insufficient funds for this withdrawal"
                )
        return data