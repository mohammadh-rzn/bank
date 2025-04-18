from locust import HttpUser, task, between, TaskSet
import random
import uuid
from typing import List, Dict

class BankApiTestUser(HttpUser):
    wait_time = between(0.5, 2)
    
    # Class-level storage for recipient users
    recipient_users: List[Dict] = []
    recipients_initialized = False
    
    def on_start(self):
        """Initialize test user and recipients once"""
        self.signup_and_login()
        self.initialize_recipients()
    
    def signup_and_login(self):
        """Create and authenticate the test user"""
        username = f"testuser_{uuid.uuid4().hex[:8]}"
        password = "testpass123"
        
        # Sign up
        self.client.post("/api/signup/", json={
            "username": username,
            "password": password,
            "password2": password,
            "balance": 10000000.00,
        })
        
        # Login to get JWT token
        response = self.client.post("/api/login/", json={
            "username": username,
            "password": password
        })
        self.token = response.json()["access"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.user_id = response.json()["user_id"]
        self.username = username
    
    def initialize_recipients(self):
        """Initialize 10 recipient users (only once across all users)"""
        if not BankApiTestUser.recipients_initialized:
            BankApiTestUser.recipients_initialized = True
            
            # Create 10 recipient accounts
            for _ in range(10):
                username = f"recipient_{uuid.uuid4().hex[:8]}"
                password = "recipient123"
                response = self.client.post("/api/signup/", json={
                    "username": username,
                    "password": password,
                    "password2": password,
                    "balance": 0.00,
                })
                
                # Login to get recipient's token
                login_resp = self.client.post("/api/login/", json={
                    "username": username,
                    "password": password
                })
                
                BankApiTestUser.recipient_users.append({
                    "user_id": login_resp.json()["user_id"],
                    "username": username,
                    "token": login_resp.json()["access"]
                })
    
    @task(5)
    def get_balance(self):
        self.client.get("/api/balance/", headers=self.headers)
    
    @task(4)
    def get_transactions(self):
        params = {"page": 1, "page_size": random.choice([5, 10, 20])}
        self.client.get("/api/transactions/", headers=self.headers, params=params)
    
    @task(3)
    def transfer_money(self):
        """Transfer to one of the pre-created recipients"""
        if not BankApiTestUser.recipient_users:
            return
            
        recipient = random.choice(BankApiTestUser.recipient_users)
        
        self.client.post("/api/transfer/", json={
            "recipient_id": recipient["user_id"],
            "amount": 0.02,
            "description": "Performance test transfer"
        }, headers=self.headers)
    
    @task(2)
    def login(self):
        """Test login with existing credentials"""
        self.client.post("/api/login/", json={
            "username": self.username,
            "password": "testpass123"
        })
    
    @task(1)
    def signup(self):
        """Test signup - still creates new users sometimes"""
        username = f"testuser_{uuid.uuid4().hex[:8]}"
        self.client.post("/api/signup/", json={
            "username": username,
            "password": "testpass123",
            "password2": "testpass123",
        })