-- Migration: 005_community.sql
-- Description: Creates tables for the Community Module

CREATE TABLE IF NOT EXISTS community_groups (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    group_type TEXT, -- e.g. "church", "mosque", "committee"
    location TEXT,
    admin_id TEXT, -- References operators.id
    trust_level TEXT DEFAULT 'local', -- 'local', 'verified', 'admin'
    preferred_channels TEXT DEFAULT 'ussd,sms',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS community_events (
    id TEXT PRIMARY KEY,
    group_id TEXT NOT NULL,
    title TEXT NOT NULL,
    event_type TEXT, -- e.g. "service", "meeting", "prayer"
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    recurrence TEXT, -- e.g. "weekly", "none"
    visibility TEXT DEFAULT 'public', -- 'public', 'members'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES community_groups (id)
);

CREATE TABLE IF NOT EXISTS community_announcements (
    id TEXT PRIMARY KEY,
    group_id TEXT NOT NULL,
    message TEXT NOT NULL,
    urgency TEXT DEFAULT 'normal', -- 'normal', 'urgent'
    expires_at DATETIME,
    target_audience TEXT DEFAULT 'public', -- 'public', 'members'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES community_groups (id)
);

CREATE TABLE IF NOT EXISTS community_inquiry_cache (
    id TEXT PRIMARY KEY,
    group_id TEXT NOT NULL,
    question_pattern TEXT NOT NULL, -- e.g. "Sunday service"
    cached_response TEXT NOT NULL,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES community_groups (id)
);
