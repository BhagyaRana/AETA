# This is the main file for the AETA project

# It Fetches the Transcripts from the website
# It Scrapes the Transcripts
# It Stores the Transcripts in a Database
# Summarizes the Transcripts
# It Stores the Summaries in a Database
# Emails the Summaries to the Users

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import re
from typing import List, Tuple, Dict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.tokenize import sent_tokenize
import nltk
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from email_function import send_summary_email

class Transcript:
    def __init__(self, stock, year, quarter, content):
        self.stock = stock
        self.year = year
        self.quarter = quarter
        self.content = content
        self.summary = None

    def __str__(self):
        return f"{self.stock.symbol} - {self.year} Q{self.quarter} Earnings Call Transcript"
    
def save_to_text_file(transcript: Transcript):
    # Save the transcript to a text file in the transcripts folder
    transcripts_folder = "transcripts"
    if not os.path.exists(transcripts_folder):
        os.makedirs(transcripts_folder)

    file_name = f"{transcripts_folder}/{transcript.stock}-{transcript.year}-Q{transcript.quarter}-transcript.txt"
    # Create the file if it doesn't exist
    if not os.path.exists(file_name):
        with open(file_name, "w", encoding='utf-8') as file:
            file.write(transcript.content)
    else:
        with open(file_name, "w", encoding='utf-8') as file:
            file.write(transcript.content)

def save_summary_to_text_file(transcript: Transcript):
    summary_folder = "summary"
    if not os.path.exists(summary_folder):
        os.makedirs(summary_folder)
    file_name = f"{summary_folder}/{transcript.stock}-{transcript.year}-Q{transcript.quarter}-transcript-summary.txt"
    with open(file_name, "w", encoding='utf-8') as file:
        file.write(transcript.summary)  


def read_from_text_file(transcript: Transcript):
    # Read the transcript from a text file
    transcripts_folder = "transcripts"
    file_name = f"{transcripts_folder}/{transcript.stock}-{transcript.year}-Q{transcript.quarter}-transcript.txt"
    with open(file_name, "r", encoding='utf-8') as file:
        content = file.read()
    return content

# Fetch the transcript from the website
def fetch_transcript(stock: str, quarter: str, year: str):
    # Note - https://www.fool.com/earnings-call-transcripts/ [The Motley Fool] url format was random and not generic, so used earningscall.ai
    url = f"https://www.earningscall.ai/stock/transcript/{stock}-{year}-Q{quarter}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        transcript_element = soup.find('div', class_='whitespace-pre-line')

        if transcript_element:
            content = transcript_element.get_text(strip=True)
            save_to_text_file(Transcript(stock, year, quarter, content))
            return Transcript(stock, year, quarter, content)
        else:
            print(f"Couldn't find transcript content for {stock} - {year} Q{quarter}\n")
            return None
    except requests.RequestException as e:
        print(f"Error fetching transcript for {stock} - {year} Q{quarter}: {e}")
        return None

# Download necessary NLTK data
nltk.download('punkt')

# Define categories and their related keywords
CATEGORIES = {
    "SUMMARY": ["revenue", "profit", "earnings", "loan growth", "credit quality", "deposits", "profitability", 
                "management", "strategy", "business verticals", "guidance", "outlook"],
    "STRATEGIC_UPDATES": ["loan growth", "credit quality", "deposits", "profitability", "strategic", "initiative"],
    "GUIDANCE_OUTLOOK": ["guidance", "outlook", "forecast", "growth", "decline", "earnings", "future"],
    "RISK_ANALYSIS": ["risk", "challenge", "mitigation", "response", "uncertainty"],
    "Q_AND_A": ["question", "answer", "ask", "respond", "clarify", "explain"]
}

def preprocess_text(text: str) -> str:
    # Remove special characters and extra spaces
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_sentences_by_category(text: str) -> Dict[str, List[str]]:
    sentences = sent_tokenize(text)
    categorized_sentences = {category: [] for category in CATEGORIES}
    
    for sentence in sentences:
        for category, keywords in CATEGORIES.items():
            if any(keyword in sentence.lower() for keyword in keywords):
                categorized_sentences[category].append(sentence)
    
    return categorized_sentences

def rank_sentences(sentences: List[str]) -> List[Tuple[str, float]]:
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(sentences)
    sentence_scores = tfidf_matrix.sum(axis=1).A1
    return list(zip(sentences, sentence_scores))

def select_top_sentences(ranked_sentences: List[Tuple[str, float]], num_sentences: int = 5) -> List[str]:
    return [sent for sent, _ in sorted(ranked_sentences, key=lambda x: x[1], reverse=True)[:num_sentences]]

def generate_abstractive_summary(text: str, max_length: int = 150) -> str:
    model_name = "facebook/bart-large-cnn"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    
    inputs = tokenizer([text], max_length=1024, return_tensors="pt", truncation=True)
    summary_ids = model.generate(inputs["input_ids"], num_beams=4, min_length=30, max_length=max_length, early_stopping=True)
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    
    return summary

def format_summary(categorized_summaries: Dict[str, str]) -> str:
    formatted_summary = ""
    
    for category, summary in categorized_summaries.items():
        formatted_summary += f"{category}\n"
        for point in summary.split(". "):
            formatted_summary += f"- {point.strip()}\n"
        formatted_summary += "\n"
    
    return formatted_summary

def summarize_financial_transcript(transcript: Transcript, num_sentences_per_category: int = 5, max_abstractive_length: int = 150) -> str:
    # Preprocess the transcript
    preprocessed_text = preprocess_text(transcript.content)
    
    # Extract sentences by category
    categorized_sentences = extract_sentences_by_category(preprocessed_text)
    
    categorized_summaries = {}
    for category, sentences in categorized_sentences.items():
        if sentences:
            # Rank the extracted sentences
            ranked_sentences = rank_sentences(sentences)
            
            # Select top sentences
            top_sentences = select_top_sentences(ranked_sentences, num_sentences_per_category)
            
            # Join the top sentences
            extractive_summary = " ".join(top_sentences)
            
            # Generate an abstractive summary
            abstractive_summary = generate_abstractive_summary(extractive_summary, max_abstractive_length)
            
            categorized_summaries[category] = abstractive_summary
    
    # Format the summary
    final_summary = format_summary(categorized_summaries)
    
    # Update the transcript object with the summary
    transcript.summary = final_summary
    
    # Save the summary to a text file
    save_summary_to_text_file(transcript)
    
    print(f"Structured summary generated for {transcript.stock} - {transcript.year} Q{transcript.quarter}")
    return final_summary


# AETA Function
def aeta_function(company: str, quarter: str, year: str):
    
    # This is a placeholder for the actual function to calculate AETA
    print(f"Running AETA for {company} in {year} Q{quarter}...")
    transcript = fetch_transcript(company, quarter, year)
    if transcript:
        print(f"Transcript fetched successfully for {company} in {year} Q{quarter}")
        # Process the transcript here
        print(f"Summarizing the transcript for {company} in {year} Q{quarter}")
        summarize_financial_transcript(transcript)
        print(f"Emailing the summary for {company} in {year} Q{quarter}")
        send_summary_email(company, year, quarter)
    else:
        print(f"Failed to fetch transcript for {company} in {year} Q{quarter}")
