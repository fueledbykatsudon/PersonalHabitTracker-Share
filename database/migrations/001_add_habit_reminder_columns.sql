-- Personal Habit Tracker & Wellness Advisor
-- Adds persistent daily reminder settings to the existing habits table.
-- Run this once in phpMyAdmin with personal_habit_tracker selected.
-- The IF NOT EXISTS clauses allow safe re-running on MariaDB versions that support them.

ALTER TABLE habits
    ADD COLUMN IF NOT EXISTS reminder_time TIME NULL DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS reminder_enabled TINYINT(1) NOT NULL DEFAULT 0;
