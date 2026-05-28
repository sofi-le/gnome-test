-- Create the table
CREATE TABLE public.gnome_dna_reports (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    session_id TEXT NOT NULL,
    file_name TEXT NOT NULL,
    report_data JSONB NOT NULL
);

-- Enable Row Level Security (RLS)
ALTER TABLE public.gnome_dna_reports ENABLE ROW LEVEL SECURITY;

-- Create policy to allow anonymous inserts (since the app currently uploads without auth)
-- WARNING: In a production app, you should require authenticated users. For a hackathon, this allows the app to work.
CREATE POLICY "Allow public inserts for hackathon" 
ON public.gnome_dna_reports 
FOR INSERT 
TO public
WITH CHECK (true);

-- Create policy to allow reading reports
CREATE POLICY "Allow public reads for hackathon" 
ON public.gnome_dna_reports 
FOR SELECT 
TO public
USING (true);
