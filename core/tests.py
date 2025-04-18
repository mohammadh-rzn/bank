from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse


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
