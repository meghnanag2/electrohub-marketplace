-- 04_user_activity.sql

-- Make sure event_type column is a reasonable size and document it
ALTER TABLE item_interactions
    ALTER COLUMN event_type TYPE VARCHAR(50);

COMMENT ON COLUMN item_interactions.event_type IS
    'Interaction type: view, save, unsave, contact, click, etc.';

-- Table to store items explicitly saved by users
CREATE TABLE IF NOT EXISTS user_saved_items (
    user_id    VARCHAR(50) REFERENCES user_accounts(user_id) ON DELETE CASCADE,
    item_id    BIGINT      REFERENCES marketplace_items(item_id) ON DELETE CASCADE,
    saved_at   TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, item_id)
);

-- Table to store contact messages sent to sellers
CREATE TABLE IF NOT EXISTS item_messages (
    message_id   BIGSERIAL PRIMARY KEY,
    item_id      BIGINT      REFERENCES marketplace_items(item_id) ON DELETE CASCADE,
    buyer_email  VARCHAR(255) NOT NULL,
    buyer_name   VARCHAR(255),
    message      TEXT         NOT NULL,
    created_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);
