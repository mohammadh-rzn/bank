from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin,AbstractUser
from django.core.validators import MinValueValidator
from django.db import transaction
from django.utils import timezone
from django.db.models import CheckConstraint, Q
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError(_('The Username must be set'))
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[AbstractUser.username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    password = models.CharField(_('password'), max_length=128)
    
    # Your existing fields
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00)]
    )
    
    # Additional required fields for authentication
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    class Meta:
        constraints = [
            CheckConstraint(
                check=Q(balance__gte=0),
                name="balance_non_negative"
            )
        ]
    
    def __str__(self):
        return self.username

    def get_full_name(self):
        return self.username

    def get_short_name(self):
        return self.username

class Transaction(models.Model):
    """
    Model to track financial transactions.
    """
    DEPOSIT = 'DEP'
    WITHDRAWAL = 'WTH'
    TRANSACTION_TYPES = [
        (DEPOSIT, 'Deposit'),
        (WITHDRAWAL, 'Withdrawal'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='transactions'
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]  # Python-level validation
    )
    transaction_type = models.CharField(
        max_length=3,
        choices=TRANSACTION_TYPES
    )
    timestamp = models.DateTimeField(default=timezone.now)
    description = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        constraints = [
            # Database-level constraint
            CheckConstraint(
                check=Q(amount__gt=0),
                name="transaction_amount_positive"
            )
        ]
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} of ${self.amount} by {self.user.username}"
    
    @classmethod
    def create_transaction(cls, user, amount, transaction_type, description=""):
        """
        Creates a transaction with proper balance validation.
        Ensures transactional integrity by using database transactions.
        """
        with transaction.atomic():
            # Lock the user's row to prevent concurrent modifications
            user = User.objects.select_for_update().get(pk=user.pk)
            
            if transaction_type == cls.WITHDRAWAL:
                if user.balance < amount:
                    raise ValueError("Insufficient funds for withdrawal")
                user.balance -= amount
            else:  # DEPOSIT
                user.balance += amount
            
            # Create the transaction record
            transaction_record = cls.objects.create(
                user=user,
                amount=amount,
                transaction_type=transaction_type,
                description=description
            )
            
            # Save the updated user balance
            user.save()
            
            return transaction_record