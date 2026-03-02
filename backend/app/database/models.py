"""SQLAlchemy database models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .models import (  # noqa: F401, PLW0406
        BillingEvent,
        Connection,
        EmailVerificationToken,
        MaxChannel,
        PaymentTransaction,
        Post,
        Subscription,
        TelegramConnection,
    )


class User(Base, TimestampMixin):
    """User model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    connections_limit: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    daily_posts_limit: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    email_verification_tokens: Mapped[list["EmailVerificationToken"]] = relationship(
        "EmailVerificationToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    telegram_connections: Mapped[list["TelegramConnection"]] = relationship(
        "TelegramConnection",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    max_channels: Mapped[list["MaxChannel"]] = relationship(
        "MaxChannel",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    connections: Mapped[list["Connection"]] = relationship(
        "Connection",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    payment_transactions: Mapped[list["PaymentTransaction"]] = relationship(
        "PaymentTransaction",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    billing_events: Mapped[list["BillingEvent"]] = relationship(
        "BillingEvent",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class EmailVerificationToken(Base, TimestampMixin):
    """Email verification token model."""

    __tablename__ = "email_verification_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="email_verification_tokens")


class TelegramConnection(Base, TimestampMixin):
    """Telegram bot connection (source) model."""

    __tablename__ = "telegram_connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    telegram_channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    telegram_channel_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bot_token: Mapped[str] = mapped_column(Text, nullable=False)  # Encrypted
    webhook_secret: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    webhook_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="telegram_connections")
    connections: Mapped[list["Connection"]] = relationship(
        "Connection",
        back_populates="telegram_connection",
        cascade="all, delete-orphan",
    )


class MaxChannel(Base, TimestampMixin):
    """Max messenger channel (destination) model."""

    __tablename__ = "max_channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    bot_token: Mapped[str] = mapped_column(Text, nullable=False)  # Encrypted
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="max_channels")
    connections: Mapped[list["Connection"]] = relationship(
        "Connection",
        back_populates="max_channel",
        cascade="all, delete-orphan",
    )


class Connection(Base, TimestampMixin):
    """Telegram to Max connection mapping model."""

    __tablename__ = "connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    telegram_connection_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("telegram_connections.id", ondelete="CASCADE"),
        nullable=False,
    )
    max_channel_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("max_channels.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="connections")
    telegram_connection: Mapped["TelegramConnection"] = relationship(
        "TelegramConnection",
        back_populates="connections",
    )
    max_channel: Mapped["MaxChannel"] = relationship(
        "MaxChannel",
        back_populates="connections",
    )
    posts: Mapped[list["Post"]] = relationship(
        "Post",
        back_populates="connection",
        cascade="all, delete-orphan",
    )
    daily_post_counts: Mapped[list["DailyPostCount"]] = relationship(
        "DailyPostCount",
        back_populates="connection",
        cascade="all, delete-orphan",
    )


class Post(Base, TimestampMixin):
    """Post history model for logging crossposting attempts."""

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    connection_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("connections.id", ondelete="CASCADE"),
        nullable=False,
    )
    telegram_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    max_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'text', 'photo', 'unsupported'
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # 'success', 'failed'
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    connection: Mapped["Connection"] = relationship("Connection", back_populates="posts")


class DailyPostCount(Base, TimestampMixin):
    """Daily post counter model for enforcing limits."""

    __tablename__ = "daily_post_counts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    connection_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("connections.id", ondelete="CASCADE"),
        nullable=False,
    )
    date: Mapped[datetime] = mapped_column(Date, nullable=False)  # Date (not datetime)
    count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Unique constraint on connection_id + date
    __table_args__ = (
        UniqueConstraint("connection_id", "date", name="uq_daily_post_count"),
    )

    # Relationships
    connection: Mapped["Connection"] = relationship("Connection", back_populates="daily_post_counts")


class Subscription(Base, TimestampMixin):
    """User subscription state for billing access control."""

    __tablename__ = "subscriptions"
    __table_args__ = (
        Index("ix_subscriptions_user_id_status", "user_id", "status"),
        Index("ix_subscriptions_provider_subscription_id", "provider_subscription_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_code: Mapped[str] = mapped_column(String(64), nullable=False, default="trial")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="trial", index=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="robokassa")
    provider_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    grace_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="subscriptions")
    payment_transactions: Mapped[list["PaymentTransaction"]] = relationship(
        "PaymentTransaction",
        back_populates="subscription",
        cascade="all, delete-orphan",
    )
    billing_events: Mapped[list["BillingEvent"]] = relationship(
        "BillingEvent",
        back_populates="subscription",
        cascade="all, delete-orphan",
    )


class PaymentTransaction(Base, TimestampMixin):
    """Incoming and outgoing payment attempts and results."""

    __tablename__ = "payment_transactions"
    __table_args__ = (
        UniqueConstraint("provider", "provider_payment_id", name="uq_payment_provider_id"),
        Index("ix_payment_transactions_user_id_status", "user_id", "status"),
        Index("ix_payment_transactions_provider_payment_id", "provider_payment_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subscription_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="robokassa")
    provider_payment_id: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="RUB")
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    raw_payload: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="payment_transactions")
    subscription: Mapped["Subscription | None"] = relationship(
        "Subscription",
        back_populates="payment_transactions",
    )
    billing_events: Mapped[list["BillingEvent"]] = relationship(
        "BillingEvent",
        back_populates="transaction",
        cascade="all, delete-orphan",
    )


class BillingEvent(Base):
    """Immutable audit trail for billing state transitions."""

    __tablename__ = "billing_events"
    __table_args__ = (
        Index("ix_billing_events_user_id_occurred_at", "user_id", "occurred_at"),
        Index("ix_billing_events_provider_event_id", "provider_event_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subscription_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
    )
    transaction_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("payment_transactions.id", ondelete="SET NULL"),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status_before: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status_after: Mapped[str | None] = mapped_column(String(32), nullable=True)
    provider_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="billing_events")
    subscription: Mapped["Subscription | None"] = relationship(
        "Subscription",
        back_populates="billing_events",
    )
    transaction: Mapped["PaymentTransaction | None"] = relationship(
        "PaymentTransaction",
        back_populates="billing_events",
    )
