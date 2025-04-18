from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import Transaction

class SignUpTest(APITestCase):
    def test_signup(self):
        url = reverse('signup')
        data = {
            'username': 'testuser',
            'password': 'StrongPassword1&',
            'password2': 'StrongPassword1&'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('username', response.data)


class LoginTest(APITestCase):
    def test_login(self):
        self.client.post(reverse('signup'), {
            'username': 'testuser',
            'password': 'StrongPassword1&',
            'password2': 'StrongPassword1&'
        })
        url = reverse('login')
        data = {
            'username': 'testuser',
            'password': 'StrongPassword1&'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)


class TransferTest(APITestCase):
    def test_transfer(self):
        self.client.post(reverse('signup'), {
            'username': 'testuser',
            'password': 'StrongPassword1&',
            'password2': 'StrongPassword1&'
        })
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'StrongPassword1&'
        })
        user_id_1 = response.data['user_id']
        self.client.post(reverse('signup'), {
            'username': 'testuser2',
            'password': 'StrongPassword1&',
            'password2': 'StrongPassword1&',
            'balance': 1000.0,
        })
        login_response = self.client.post(reverse('login'), {
            'username': 'testuser2',
            'password': 'StrongPassword1&'
        })
        access_token = login_response.data['access']

        url = reverse('transfer')
        data = {
            'recipient_id': user_id_1,
            'amount': 100.0
        }
        response = self.client.post(url, data, HTTP_AUTHORIZATION=f'Bearer {access_token}', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TransactionsTest(APITestCase):
    def test_transactions(self):
        self.client.post(reverse('signup'), {
            'username': 'testuser',
            'password': 'StrongPassword1&',
            'password2': 'StrongPassword1&'
        })
        login_response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'StrongPassword1&'
        })
        access_token = login_response.data['access']

        url = reverse('user-transactions')
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {access_token}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data['results'], list)


class BalanceTest(APITestCase):
    def test_balance(self):
        self.client.post(reverse('signup'), {
            'username': 'testuser',
            'password': 'StrongPassword1&',
            'password2': 'StrongPassword1&'
        })
        login_response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'StrongPassword1&'
        })
        access_token = login_response.data['access']

        url = reverse('user-balance')
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {access_token}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('balance', response.data)

class RateLimitTest(APITestCase):
    def test_rate_limit(self):
        self.client.post(reverse('signup'), {
            'username': 'testuser',
            'password': 'StrongPassword1&',
            'password2': 'StrongPassword1&'
        })
        login_response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'StrongPassword1&'
        })
        access_token = login_response.data['access']

        url = reverse('user-balance')
        for _ in range(9):  # Assuming the limit is 10 requests
            response = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {access_token}', format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Now test exceeding the limit
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {access_token}', format='json')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        
import pytest
from django.urls import reverse
from background_task.models import Task
from freezegun import freeze_time
from datetime import timedelta
from django.utils import timezone

@pytest.mark.django_db
class LoginBackgroundTasksTest(TestCase):
    def test_login_triggers_background_task(self, client, mocker):
        """Test that login creates a background task"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Setup test user
        user = User.objects.create_user(
            username='testuser',
            password='testpass',
            balance=1000.00
        )

        # Mock the actual task function to skip real processing
        mock_task = mocker.patch('core.tasks.process_login_transactions')

        # Make login request
        url = reverse('login')
        with freeze_time('2023-01-01'):
            response = client.post(url, {
                'username': 'testuser',
                'password': 'testpass'
            })

        # Verify HTTP response
        assert response.status_code == 200
        assert 'access' in response.data

        # Verify task was created
        tasks = Task.objects.all()
        assert tasks.count() == 1
        assert tasks[0].task_name == 'yourapp.tasks.process_login_transactions'
        assert tasks[0].task_params == f'[[{user.id}], {{}}]'  # Serialized params

        # Verify task would run at correct time (if not mocked)
        assert tasks[0].run_at == timezone.now()

    def test_background_task_execution(self, mocker):
        """Test the actual task processing"""
        from core.tasks import process_login_transactions
        from core.models import User, Transaction
        
        # Create test user
        user = User.objects.create_user(
            username='taskuser',
            password='testpass',
            balance=1000.00
        )

        # Execute task directly (mocking would skip this)
        result = process_login_transactions(user.id)

        # Verify task results
        user.refresh_from_db()
        transactions = Transaction.objects.filter(user=user)
        assert transactions.exists()
        assert user.balance != 1000.00  # Balance should change
        assert result['status'] == 'success'