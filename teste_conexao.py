import streamlit as st
from supabase import create_client

url = "https://igdrosjxrzbknpodqvgu.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlnZHJvc2p4cnpia25wb2Rxdmd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI3MTM4ODIsImV4cCI6MjA4ODI4OTg4Mn0.h7ZTqAiTOAd6r14rTHAIgF-hPoTwb3oj8sujx6zC-2E"

supabase = create_client(url, key)
response = supabase.table("veiculos").select("*").execute()
print(response.data)