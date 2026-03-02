-- Billing MVP baseline schema.
-- Safe to run multiple times due IF NOT EXISTS guards.

CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_code VARCHAR(64) NOT NULL DEFAULT 'trial',
    status VARCHAR(32) NOT NULL DEFAULT 'trial',
    provider VARCHAR(32) NOT NULL DEFAULT 'robokassa',
    provider_customer_id VARCHAR(255),
    provider_subscription_id VARCHAR(255),
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    trial_ends_at TIMESTAMPTZ,
    grace_ends_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS payment_transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id INTEGER REFERENCES subscriptions(id) ON DELETE SET NULL,
    provider VARCHAR(32) NOT NULL DEFAULT 'robokassa',
    provider_payment_id VARCHAR(255) NOT NULL,
    status VARCHAR(32) NOT NULL,
    amount_minor BIGINT NOT NULL,
    currency VARCHAR(8) NOT NULL DEFAULT 'RUB',
    idempotency_key VARCHAR(255) UNIQUE,
    raw_payload TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_payment_provider_id UNIQUE (provider, provider_payment_id)
);

CREATE TABLE IF NOT EXISTS billing_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id INTEGER REFERENCES subscriptions(id) ON DELETE SET NULL,
    transaction_id INTEGER REFERENCES payment_transactions(id) ON DELETE SET NULL,
    event_type VARCHAR(64) NOT NULL,
    status_before VARCHAR(32),
    status_after VARCHAR(32),
    provider_event_id VARCHAR(255),
    occurred_at TIMESTAMPTZ NOT NULL,
    payload_json TEXT
);

CREATE INDEX IF NOT EXISTS ix_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS ix_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS ix_subscriptions_user_id_status ON subscriptions(user_id, status);
CREATE INDEX IF NOT EXISTS ix_subscriptions_provider_subscription_id ON subscriptions(provider_subscription_id);

CREATE INDEX IF NOT EXISTS ix_payment_transactions_user_id ON payment_transactions(user_id);
CREATE INDEX IF NOT EXISTS ix_payment_transactions_status ON payment_transactions(status);
CREATE INDEX IF NOT EXISTS ix_payment_transactions_user_id_status ON payment_transactions(user_id, status);
CREATE INDEX IF NOT EXISTS ix_payment_transactions_provider_payment_id ON payment_transactions(provider_payment_id);

CREATE INDEX IF NOT EXISTS ix_billing_events_user_id ON billing_events(user_id);
CREATE INDEX IF NOT EXISTS ix_billing_events_user_id_occurred_at ON billing_events(user_id, occurred_at);
CREATE INDEX IF NOT EXISTS ix_billing_events_provider_event_id ON billing_events(provider_event_id);
