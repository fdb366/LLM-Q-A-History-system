SET FOREIGN_KEY_CHECKS = 0;
DELETE FROM messages;
DELETE FROM conversations;
DELETE FROM users;
SET FOREIGN_KEY_CHECKS = 1;
SELECT 'Data cleared successfully' AS result;


-- 
-- Get-Content scripts/clear_users_simple.sql | mysql -u history_user -pHistory@2023 -h localhost -P 3306 history_qa
-- 