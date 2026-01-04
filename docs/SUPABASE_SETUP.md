# UceAsistan Supabase Setup Guide

## 1. Supabase Projesi Oluşturma

1. [supabase.com](https://supabase.com) adresine gidin
2. "Start your project" butonuna tıklayın
3. GitHub ile giriş yapın
4. "New Project" butonuna tıklayın
5. Proje bilgilerini girin:
   - **Name**: `uceasistan`
   - **Database Password**: Güçlü bir şifre belirleyin (kaydedin!)
   - **Region**: `Frankfurt (eu-central-1)` - Türkiye'ye en yakın

## 2. API Anahtarlarını Alma

Project Settings > API bölümünden:

```
SUPABASE_URL = https://xxxxx.supabase.co
SUPABASE_ANON_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 3. Auth Ayarları

Authentication > Providers bölümünden:
- ✅ Email (varsayılan açık)
- ❌ Phone (kapalı tut)
- Opsiyonel: Google, GitHub OAuth

Authentication > URL Configuration:
```
Site URL: https://uceasistan.vercel.app
Redirect URLs: 
  - https://uceasistan.vercel.app/app
  - http://localhost:8000/index.html
```

## 4. Veritabanı Tabloları

SQL Editor'de çalıştırın:

```sql
-- Users Profile Table
CREATE TABLE profiles (
  id UUID REFERENCES auth.users ON DELETE CASCADE,
  email TEXT,
  full_name TEXT,
  subscription_tier TEXT DEFAULT 'free',
  subscription_expires_at TIMESTAMP WITH TIME ZONE,
  ai_requests_used INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  PRIMARY KEY (id)
);

-- Enable Row Level Security
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own profile
CREATE POLICY "Users can view own profile" ON profiles
  FOR SELECT USING (auth.uid() = id);

-- Policy: Users can update own profile
CREATE POLICY "Users can update own profile" ON profiles
  FOR UPDATE USING (auth.uid() = id);

-- Automatically create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name)
  VALUES (NEW.id, NEW.email, NEW.raw_user_meta_data->>'full_name');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Newsletter Subscribers Table
CREATE TABLE newsletter_subscribers (
  id SERIAL PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  source TEXT DEFAULT 'website',
  subscribed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  is_active BOOLEAN DEFAULT TRUE
);

-- Strategies Table
CREATE TABLE user_strategies (
  id SERIAL PRIMARY KEY,
  user_id UUID REFERENCES auth.users ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  code TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE user_strategies ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own strategies" ON user_strategies
  FOR ALL USING (auth.uid() = user_id);
```

## 5. Frontend Entegrasyonu

`auth.js` dosyasında şu değişkenleri güncelleyin:

```javascript
this.supabaseUrl = 'YOUR_SUPABASE_URL';
this.supabaseKey = 'YOUR_SUPABASE_ANON_KEY';
```

## 6. Test Etme

1. Landing page'den "Ücretsiz Başla" butonuna tıklayın
2. Yeni bir hesap oluşturun
3. E-posta onayı alın (Supabase bunu otomatik yapar)
4. Giriş yapın

## Güvenlik Notları

⚠️ **ÖNEMLİ**:
- `SUPABASE_ANON_KEY` frontend'de kullanılabilir (public)
- `SUPABASE_SERVICE_ROLE_KEY` sadece backend'de kullanılmalı (gizli)
- Row Level Security (RLS) HER ZAMAN aktif olmalı
- API anahtarlarını GitHub'a commit etmeyin
