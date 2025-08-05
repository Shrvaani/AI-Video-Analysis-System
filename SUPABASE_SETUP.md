# 🚀 Supabase Setup Guide for AI Video Analysis System

## 📋 Prerequisites
- A Supabase account (free tier available at [supabase.com](https://supabase.com))
- Your AI Video Analysis System code

## 🛠️ Step-by-Step Setup

### 1. Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign up/login
2. Click "New Project"
3. Choose your organization
4. Enter project details:
   - **Name**: `ai-video-analysis-system`
   - **Database Password**: Choose a strong password
   - **Region**: Select closest to your users
5. Click "Create new project"
6. Wait for the project to be created (2-3 minutes)

### 2. Get Your Project Credentials

1. In your Supabase dashboard, go to **Settings** → **API**
2. Copy these values:
   - **Project URL** (looks like: `https://your-project-id.supabase.co`)
   - **Anon public key** (starts with `eyJ...`)

### 3. Set Up Environment Variables

Create a `.env` file in your project root:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
```

### 4. Set Up the Database Schema

1. In your Supabase dashboard, go to **SQL Editor**
2. Copy the contents of `supabase_schema.sql`
3. Paste and run the SQL commands
4. Verify the tables are created in **Table Editor**

### 5. Configure Storage

1. Go to **Storage** in your Supabase dashboard
2. The `video-analysis` bucket should be created automatically
3. If not, create it manually:
   - **Name**: `video-analysis`
   - **Public bucket**: ✅ Checked
   - **File size limit**: 50MB (or your preferred limit)

### 6. Test the Connection

1. Add the environment variables to your Streamlit Cloud deployment
2. Deploy your app
3. Check if you see "✅ Connected to Supabase successfully!" message

## 🔧 Environment Variables for Streamlit Cloud

When deploying to Streamlit Cloud, add these secrets:

1. Go to your app settings in Streamlit Cloud
2. Add these secrets:
   ```
   SUPABASE_URL = https://your-project-id.supabase.co
   SUPABASE_ANON_KEY = your-anon-key-here
   ```

## 📊 Database Tables Created

The schema creates these tables:

- **sessions**: Video processing sessions
- **persons**: Detected and identified persons
- **face_images**: Face image metadata
- **videos**: Video file metadata
- **payment_results**: Payment detection results

## 🗂️ Storage Structure

Files are stored in the `video-analysis` bucket:

```
video-analysis/
├── faces/
│   └── {session_id}/
│       └── {person_id}/
│           ├── first_detection.jpg
│           └── frame_*.jpg
└── videos/
    └── {session_id}/
        └── {video_filename}
```

## 🔒 Security Considerations

- The current setup allows public access to all data
- For production, consider adding authentication
- You can modify RLS policies in Supabase dashboard

## 🚨 Troubleshooting

### Connection Issues
- Verify your environment variables are correct
- Check if your Supabase project is active
- Ensure the schema has been applied

### Storage Issues
- Verify the `video-analysis` bucket exists
- Check storage policies are set correctly
- Monitor storage usage in Supabase dashboard

### Database Issues
- Check if all tables were created successfully
- Verify foreign key relationships
- Monitor database usage and performance

## 📈 Monitoring

Monitor your Supabase usage in the dashboard:
- **Database**: Query performance, storage usage
- **Storage**: File uploads, bandwidth usage
- **API**: Request counts, response times

## 💰 Cost Considerations

Supabase free tier includes:
- 500MB database
- 1GB file storage
- 2GB bandwidth
- 50,000 monthly active users

For production use, consider upgrading to Pro plan.

## 🔄 Migration from Local Storage

The app will automatically:
1. Save new data to Supabase
2. Load existing data from Supabase
3. Fall back to local storage if Supabase is unavailable

## 📞 Support

- Supabase Documentation: [supabase.com/docs](https://supabase.com/docs)
- Supabase Community: [github.com/supabase/supabase](https://github.com/supabase/supabase)
- Streamlit Community: [discuss.streamlit.io](https://discuss.streamlit.io) 