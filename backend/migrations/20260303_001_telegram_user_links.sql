-- Telegram user account linking for onboarding bot commands.

CREATE TABLE IF NOT EXISTS telegram_user_links (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    telegram_user_id BIGINT NOT NULL,
    telegram_username VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_telegram_user_links_user_id UNIQUE (user_id),
    CONSTRAINT uq_telegram_user_links_telegram_user_id UNIQUE (telegram_user_id)
);

CREATE INDEX IF NOT EXISTS ix_telegram_user_links_user_id
    ON telegram_user_links(user_id);

CREATE INDEX IF NOT EXISTS ix_telegram_user_links_telegram_user_id
    ON telegram_user_links(telegram_user_id);
