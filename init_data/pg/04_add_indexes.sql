-- チャット機能の高速化用インデックス

-- 未読メッセージ検索用（receiver_id, is_read, sender_id の複合インデックス）
CREATE INDEX IF NOT EXISTS idx_chat_messages_receiver_unread
ON chat_messages(receiver_id, is_read, sender_id)
WHERE is_read = FALSE;

-- メッセージ履歴取得用（sender/receiverの組み合わせとタイムスタンプ）
CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation
ON chat_messages(sender_id, receiver_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation_reverse
ON chat_messages(receiver_id, sender_id, created_at DESC);
