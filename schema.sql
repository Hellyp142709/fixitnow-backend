-- FixitNow Database Schema
-- Run this in your Supabase SQL Editor

-- Users table
CREATE TABLE IF NOT EXISTS users (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  phone TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  joined_at TIMESTAMPTZ DEFAULT NOW()
);

-- Sessions table (for auth tokens)
CREATE TABLE IF NOT EXISTS sessions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  token TEXT UNIQUE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bookings table
CREATE TABLE IF NOT EXISTS bookings (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  pro_id INTEGER NOT NULL,
  pro_name TEXT NOT NULL,
  pro_avatar TEXT,
  pro_rating DECIMAL(3,2),
  pro_price TEXT,
  service_id TEXT NOT NULL,
  service_label TEXT NOT NULL,
  date TEXT NOT NULL,
  time TEXT NOT NULL,
  address TEXT NOT NULL,
  emergency BOOLEAN DEFAULT FALSE,
  notes TEXT DEFAULT '',
  eta TEXT,
  status TEXT DEFAULT 'upcoming',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Saved professionals table
CREATE TABLE IF NOT EXISTS saved_pros (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  pro_id INTEGER NOT NULL,
  pro_name TEXT NOT NULL,
  pro_avatar TEXT,
  pro_rating DECIMAL(3,2),
  pro_price TEXT,
  pro_service TEXT,
  saved_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, pro_id)
);

-- Row Level Security (RLS) - optional but recommended
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE bookings ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE saved_pros ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
