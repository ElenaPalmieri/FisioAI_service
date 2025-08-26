from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import os
import pymongo
from datetime import datetime, timedelta

import nltk
from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import word_tokenize, sent_tokenize

# from openai import OpenAI
# import google.generativeai as genai


# CONFIGURATION
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "FisioDB")

app = FastAPI(title="AI Service")


# Returns the MongoDB Client
def get_db_client(uri: str = MONGO_URI) -> pymongo.MongoClient:
    return pymongo.MongoClient(uri)


# INITIALIZATIONS
# Only need to be downloaded once
nltk.download('stopwords', quiet=True)
nltk.download('punkt_tab', quiet=True)

# Initialization of the stopwords
stopwords = nltk.corpus.stopwords.words('italian')

# Initialization of the stemmer
stemmer = SnowballStemmer("italian", True)


# Definition of improvement keywords
IMPROVEMENT_KEYWORDS = {
    "miglioramento", "miglioramenti", "migliorata", "migliorato", "migliorare",
    "recupero", "recuperata", "recuperato",
    "risoluzione", "risolta", "risolto",
    "riduzione", "ridotto", "diminuito", "diminuire", "calato",
    "progressi", "migliore", "meglio",
    "ottimi", "ottimo", "eccellente", "benissimo"
}


# Returns Ture if the sentence contains improvement keywords
def is_improvement(sentence: str) -> bool:
    words = word_tokenize(sentence.lower(), language="italian")
    return any(word in IMPROVEMENT_KEYWORDS for word in words)


# Returns the sentences that contain improvements
def extract_improvement_sentences(text: str) -> List[str]:
    sentences = sent_tokenize(text, language="italian")
    return [s for s in sentences if is_improvement(s)]


# # Call to GPT
# def ask_gpt(text):
#
#     # Setting up the OpenAI client
#     client = OpenAI(
#         # This is the default and can be omitted
#         api_key=os.environ.get("OPENAI_API_KEY"),
#     )
#
#     # Standard prompt for every call
#     gpt_prompt = """Ti fornirò un testo che contiene frasi che riguardano il progresso del trattamento fisioterapico di un paziente.
#     Il tuo compito è quello di analizzare il testo e capire se si riferisce a un paziente con dolore lombare che ha mostrato segni di miglioramento.
#     L'output deve essere esclusivamente "yes" in caso affermativo, o "no" in caso negativo.
#
#     Esempio di testo in input:
#     "Riferisce forte dolore nella zona lombare, soprattutto al mattino. Difficoltà nelle attività quotidiane. Dopo la seduta il paziente riferisce una netta diminuzione del dolore"
#
#     Esempio di output:
#     "yes"
#
#     Ora analizza il seguente testo:
#     """
#
#     stream = client.chat.completions.create(
#         model="gpt-4o",
#         messages=[{"role": "user", "content": gpt_prompt + "\n" + text}],
#         stream=True,
#     )
#
#     # Collecting the answer from the stream
#     gpt_answer = ''
#     for chunk in stream:
#         gpt_answer += str(chunk.choices[0].delta.content or "")
#
#     return "yes" in gpt_answer.lower()
#
#
# # Call to Gemini
# def ask_gemini(text):
#
#     # Configuration
#     genai.configure(api_key="GEMINI_KEY")
#     model = genai.GenerativeModel('gemini-1.5-flash-latest')
#
#     # Standard prompt for every call
#     gemini_prompt = """Ti fornirò un testo che contiene frasi che riguardano il progresso del trattamento fisioterapico di un paziente.
#         Il tuo compito è quello di analizzare il testo e capire se si riferisce a un paziente con dolore lombare che ha mostrato segni di miglioramento.
#         L'output deve essere esclusivamente "yes" in caso affermativo, o "no" in caso negativo.
#
#         Esempio di testo in input:
#         "Riferisce forte dolore nella zona lombare, soprattutto al mattino. Difficoltà nelle attività quotidiane. Dopo la seduta il paziente riferisce una netta diminuzione del dolore"
#
#         Esempio di output:
#         "yes"
#
#         Ora analizza il seguente testo:
#         """
#
#     # Collecting Gemini's answer
#     gemini_answer = model.generate_content(gemini_prompt + text)
#
#     return "yes" in gemini_answer.text.lower()


# Creating the class for the results
class AnalyzeResponse(BaseModel):
    paziente_id: str
    nome: str
    cognome: str
    telefono: str
    data_appuntamento_saltato: datetime


def analyze_records():
    # Connection to the database
    client = get_db_client()
    db = client[DB_NAME]

    pazienti = db["pazienti"]
    calendario = db['calendario']
    schede_valutazione = db['schede_valutazione']
    diario_trattamenti = db['diario_trattamenti']

    # TODO: Questo è modificato per avere un po' di entry utili, rimettere days=90
    three_months_ago = datetime.now() - timedelta(days=500)

    # Variable containing the results
    results: List[AnalyzeResponse] = []

    # Find all the active patients in the DB and cycle them one by one
    for paziente in pazienti.find({"stato": "attivo"}):

        # Find all the appointments of that patient
        appuntamenti = list(calendario.find({"paziente_id": paziente["_id"]}))

        # If there are no appointments for the patient there is no point in checking anything
        # If there is only one appointment either the patient showed, or there is no record of symptoms and improvement
        if not appuntamenti:
            continue

        # Finding the most recent appointment
        most_recent = max(appuntamenti, key=lambda x: x['data'])

        # Filter the patients who skipped last appointment
        # The check on the last appointment to be within the last 3 months allows to avoid useless computation
        if three_months_ago <= most_recent['data'] and most_recent['stato'] in ['no_show', 'cancellato']:

            # Creating a single string with all the descriptions from the last three months
            descrizioni = ''

            # Collecting all the descriptions from schede_valutazione
            for scheda in schede_valutazione.find({"paziente_id": most_recent["paziente_id"]}):
                if three_months_ago <= scheda['data']:
                    descrizioni = descrizioni + scheda['descrizione'] + '\n'

            # Collecting all the descriptions from diario_trattamenti
            for diario in diario_trattamenti.find({"paziente_id": most_recent["paziente_id"]}):
                if three_months_ago <= diario['data']:
                    descrizioni = descrizioni + diario['descrizione'] + '\n'

            # Searching for mentions of "dolore lombare" without AI
            # Tokenization
            words = word_tokenize(descrizioni)

            # Stemming
            stemmed_words = [stemmer.stem(word) for word in words]

            # The stemmed keywords "lombare" and "lombalgia" should cover all the cases
            if stemmer.stem("lombare") in stemmed_words or stemmer.stem("lombalgia") in stemmed_words or stemmer.stem("schiena") in stemmed_words:

                # Finding the sentences that contain improvement keywords without AI
                # Note that these sentences could contain sentences such as "nessun miglioramento significativo"
                improvements = extract_improvement_sentences(descrizioni)

                # Removing the sentences that contain "non" or "nessuno"/"nessuna"/"nessun"
                cleaned_improvements = []
                for improvement in improvements:
                    words = word_tokenize(improvement.lower())
                    stemmed_words = [stemmer.stem(word) for word in words]
                    if "non" not in improvement.lower() and stemmer.stem("nessuno") not in stemmed_words:
                        cleaned_improvements.append(improvement)
                # cleaned_improvements = [improvement for improvement in improvements if "non" not in improvement.lower() and stemmer.stem("nessuno") not in [stemmer.stem(w) for w in word_tokenize(improvement.lower())]]

                # If nothing was found, double check using AI
                # if cleaned_results or ask_gemini(descrizioni):
                if cleaned_improvements:
                    results.append({
                        "patient_id": str(paziente["_id"]),
                        "nome": paziente["nome"],
                        "cognome": paziente["cognome"],
                        "telefono": paziente["telefono"],
                        "data_appuntamento_saltato": most_recent["data"]
                    })

    client.close()
    return results


if __name__ == "__main__":
    for result in analyze_records():
        print(result)