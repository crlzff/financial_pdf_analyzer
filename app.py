import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import PyPDF2
from datetime import datetime
import re

# Configurazione pagina
st.set_page_config(
    page_title="Analizzatore PDF Finanziari",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Titolo e descrizione
st.title("📊 Analizzatore di Documenti Finanziari")
st.markdown("Carica PDF finanziari o fornisci URL per estrarre e analizzare metriche finanziarie chiave di più aziende.")

# Configurazione sidebar
st.sidebar.header("🔧 Configurazione")

# Debug mode toggle
debug_mode = st.sidebar.checkbox(
    "🐛 Modalità Debug",
    value=False,
    help="Mostra risposte complete dell'AI e informazioni dettagliate di debug"
)

if debug_mode:
    st.sidebar.info("🐛 **Modalità Debug Attiva**\n\nVedrai informazioni dettagliate su:\n- Testo estratto dai PDF\n- Prompt inviati all'AI\n- Risposte complete dell'AI\n- Parsing JSON\n- Statistiche di elaborazione")

# Configurazione API OpenRouter
openrouter_api_key = st.sidebar.text_input(
    "Chiave API OpenRouter",
    type="password",
    help="Inserisci la tua chiave API OpenRouter",
    placeholder="Inserisci la chiave API..."
)

# Validazione chiave API
if openrouter_api_key:
    if len(openrouter_api_key.strip()) < 10:
        st.sidebar.error("⚠️ La chiave API sembra troppo corta")
    else:
        st.sidebar.success("✅ Chiave API configurata")

# Selezione modello (aggiornata con i modelli richiesti)
model_options = [
    "anthropic/claude-sonnet-4",
    "anthropic/claude-opus-4", 
    "google/gemini-2.5-flash-preview-05-20",
    "google/gemini-2.5-pro-preview",
    "openai/gpt-4.1"
]

selected_model = st.sidebar.selectbox(
    "Seleziona Modello AI",
    model_options,
    index=0,
    help="Scegli il modello AI per l'analisi dei documenti"
)

# Selezione metriche finanziarie
st.sidebar.header("📈 Metriche da Estrarre")
available_metrics = [
    "Ricavi/Vendite",
    "EBITDA", 
    "EBIT",
    "Utile Netto",
    "Totale Attività",
    "Totale Passività", 
    "Patrimonio Netto",
    "Flusso di Cassa Operativo",
    "Free Cash Flow",
    "Rapporto Debito/Patrimonio",
    "PFN (Posizione Finanziaria Netta)"
]

selected_metrics = st.sidebar.multiselect(
    "Scegli le metriche da estrarre:",
    available_metrics,
    default=["EBITDA", "EBIT", "PFN (Posizione Finanziaria Netta)"],
    help="Seleziona le metriche finanziarie che vuoi estrarre dai documenti"
)

# Funzione per estrarre testo da PDF
def extract_pdf_text(pdf_file):
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Errore nell'estrazione del testo dal PDF: {str(e)}")
        return None

# Funzione per chiamare API OpenRouter (implementazione sicura)
def call_openrouter_api(prompt, model=None):
    # Validazione chiave API
    if not openrouter_api_key or len(openrouter_api_key.strip()) < 10:
        st.error("❌ Inserisci una chiave API OpenRouter valida nella barra laterale.")
        return None
    
    # Usa il modello selezionato
    if not model:
        model = selected_model
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {openrouter_api_key.strip()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://analizzatore-pdf-finanziari.streamlit.app",
        "X-Title": "Analizzatore PDF Finanziari"
    }
    
    data = {
        "model": model,
        "messages": [
            {
                "role": "user", 
                "content": prompt
            }
        ],
        "max_tokens": 4000,
        "temperature": 0.1
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        else:
            st.error("❌ Risposta API non valida")
            return None
            
    except requests.exceptions.Timeout:
        st.error("❌ Timeout della richiesta API. Riprova.")
        return None
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            st.error("❌ Chiave API non valida. Controlla le tue credenziali OpenRouter.")
        elif response.status_code == 402:
            st.error("❌ Credito API insufficiente. Ricarica il tuo account OpenRouter.")
        elif response.status_code == 429:
            st.error("❌ Troppi richieste. Attendi un momento e riprova.")
        else:
            st.error(f"❌ Errore API HTTP {response.status_code}: {str(e)}")
        return None
    except Exception as e:
        st.error(f"❌ Errore nella chiamata API OpenRouter: {str(e)}")
        return None

# Funzione per estrarre JSON da risposta AI
def extract_json_from_response(response_text):
    """Estrae JSON da una risposta che potrebbe contenere testo aggiuntivo"""
    if not response_text:
        return None
    
    # Cerca il primo { e l'ultimo }
    start = response_text.find('{')
    end = response_text.rfind('}')
    
    if start != -1 and end != -1 and end > start:
        json_str = response_text[start:end+1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None
    return None

# Funzione per identificare azienda e anno
def identify_company_and_year(pdf_text):
    prompt = f"""
    Analizza questo documento finanziario e identifica le informazioni richieste.
    
    IMPORTANTE: Restituisci SOLO il JSON richiesto, senza altro testo.
    
    Formato richiesto:
    {{
        "company_name": "Nome Azienda S.p.A.",
        "fiscal_year": "2023", 
        "currency": "EUR",
        "document_type": "Relazione Annuale"
    }}
    
    Cerca nel documento:
    1. Nome dell'azienda (nome legale completo)
    2. Anno fiscale o periodo coperto
    3. Valuta utilizzata nei bilanci
    4. Tipo di documento (relazione annuale, bilancio, ecc.)
    
    Testo del documento (primi 3000 caratteri):
    {pdf_text[:3000]}
    """
    
    return call_openrouter_api(prompt)

# Funzione per estrarre dati finanziari
def extract_financial_data(pdf_text, company_info, metrics):
    metrics_str = ", ".join(metrics)
    
    prompt = f"""
    Estrai le metriche finanziarie richieste da questo documento.
    
    IMPORTANTE: Restituisci SOLO il JSON richiesto, senza altro testo o spiegazioni.
    
    Azienda: {company_info.get('company_name', 'azienda')}
    Anno fiscale: {company_info.get('fiscal_year', 'sconosciuto')}
    Metriche da estrarre: {metrics_str}
    
    Formato richiesto:
    {{
        "Ricavi/Vendite": {{"value": 123456789, "unit": "milioni"}},
        "EBITDA": {{"value": 23456789, "unit": "milioni"}},
        "EBIT": {{"value": 20000000, "unit": "milioni"}},
        "PFN (Posizione Finanziaria Netta)": {{"value": 15000000, "unit": "milioni"}}
    }}
    
    Regole specifiche:
    - Converti tutti i valori nella stessa unità (preferibilmente milioni)
    - Se una metrica non viene trovata direttamente, CALCOLALA dai dati disponibili:
      * EBITDA = EBIT + Ammortamenti (ammort. immateriali + ammort. materiali)
      * EBIT = Risultato operativo (A-B nel conto economico italiano)
      * PFN = Debiti verso banche - Disponibilità liquide - Titoli facilmente liquidabili
      * Se PFN è negativo = posizione di liquidità netta (bene per l'azienda)
    - Per i rapporti, usa il formato decimale (es. 0.25 per 25%)
    - Cerca in tutto il documento, non solo all'inizio
    - Identifica voci come "Ricavi delle vendite", "TOTALE VALORE DELLA PRODUZIONE", "TOTALE COSTI DELLA PRODUZIONE"
    - Per ammortamenti cerca "AMM.TO" o "ammortamenti"
    - Per debiti bancari cerca "Debiti verso banche"
    - Per liquidità cerca "Disponibilità liquide" o "Depositi bancari"
    
    Testo del documento (primi 20000 caratteri):
    {pdf_text[:20000]}
    """
    
    return call_openrouter_api(prompt)

# Interfaccia principale dell'app
st.header("📁 Carica Documenti")

# Upload dei file PDF
uploaded_files = st.file_uploader(
    "Carica Relazioni Finanziarie",
    type="pdf",
    accept_multiple_files=True,
    help="Carica uno o più documenti finanziari PDF"
)

pdf_sources = []

if uploaded_files:
    for file in uploaded_files:
        pdf_sources.append({
            "name": file.name,
            "content": file,
            "source": "upload"
        })

# Elaborazione documenti
if pdf_sources and selected_metrics and openrouter_api_key:
    st.header("🔄 Elaborazione Documenti")
    
    if st.button("🚀 Analizza Documenti Finanziari", type="primary"):
        results = {}
        
        # Tracciamento progresso
        total_docs = len(pdf_sources)
        progress_bar = st.progress(0)
        status_container = st.container()
        
        # Container per debug (se abilitato)
        if debug_mode:
            debug_container = st.container()
            debug_container.header("🐛 Debug Panel")
        
        for i, pdf_source in enumerate(pdf_sources):
            with status_container:
                st.write(f"📄 Elaborando: {pdf_source['name']}")
            
            # Debug: Informazioni documento
            if debug_mode:
                with debug_container:
                    with st.expander(f"🔍 Debug: {pdf_source['name']}", expanded=False):
                        st.write(f"**Nome file**: {pdf_source['name']}")
                        st.write(f"**Sorgente**: File caricato")
            
            # Estrai testo dal PDF
            pdf_text = extract_pdf_text(pdf_source['content'])
            
            # Debug: Testo estratto
            if debug_mode and pdf_text:
                with debug_container:
                    with st.expander(f"📄 Testo estratto da {pdf_source['name']}", expanded=False):
                        st.write(f"**Lunghezza testo**: {len(pdf_text)} caratteri")
                        st.write(f"**Prime 1000 caratteri**:")
                        st.text(pdf_text[:1000])
                        st.write(f"**Ultime 500 caratteri**:")
                        st.text(pdf_text[-500:])
            
            if pdf_text and len(pdf_text.strip()) > 100:  # Assicurati che ci sia testo significativo
                # Passo 1: Identifica azienda e anno
                with st.spinner(f"🔍 Identificando azienda per {pdf_source['name']}..."):
                    company_response = identify_company_and_year(pdf_text)
                
                # Debug: Risposta identificazione azienda
                if debug_mode:
                    with debug_container:
                        with st.expander(f"🏢 Debug Identificazione Azienda: {pdf_source['name']}", expanded=False):
                            st.write("**Prompt inviato all'AI:**")
                            prompt_preview = f"""
Analizza questo documento finanziario e identifica le informazioni richieste.

IMPORTANTE: Restituisci SOLO il JSON richiesto, senza altro testo.

Formato richiesto:
{{
    "company_name": "Nome Azienda S.p.A.",
    "fiscal_year": "2023", 
    "currency": "EUR",
    "document_type": "Relazione Annuale"
}}

Testo del documento (primi 3000 caratteri):
{pdf_text[:200]}...[TRONCATO]
                            """
                            st.code(prompt_preview, language="text")
                            
                            st.write("**Risposta completa dell'AI:**")
                            if company_response:
                                st.text(company_response)
                            else:
                                st.error("Nessuna risposta ricevuta")
                
                if company_response:
                    # Prova a estrarre JSON dalla risposta
                    company_info = extract_json_from_response(company_response)
                    
                    # Debug: Parsing JSON azienda
                    if debug_mode:
                        with debug_container:
                            with st.expander(f"🔧 Debug JSON Parsing Azienda: {pdf_source['name']}", expanded=False):
                                st.write("**JSON estratto:**")
                                if company_info:
                                    st.json(company_info)
                                else:
                                    st.error("Impossibile estrarre JSON valido dalla risposta")
                    
                    if company_info:
                        company_name = company_info.get('company_name', f'Azienda Sconosciuta {i+1}')
                        
                        # Passo 2: Estrai dati finanziari
                        with st.spinner(f"💰 Estraendo dati finanziari per {company_name}..."):
                            financial_response = extract_financial_data(pdf_text, company_info, selected_metrics)
                        
                        # Debug: Risposta estrazione finanziaria
                        if debug_mode:
                            with debug_container:
                                with st.expander(f"💰 Debug Estrazione Finanziaria: {company_name}", expanded=False):
                                    st.write("**Prompt inviato all'AI:**")
                                    metrics_str = ", ".join(selected_metrics)
                                    prompt_preview = f"""
Estrai le metriche finanziarie richieste da questo documento.

IMPORTANTE: Restituisci SOLO il JSON richiesto, senza altro testo o spiegazioni.

Azienda: {company_name}
Anno fiscale: {company_info.get('fiscal_year', 'sconosciuto')}
Metriche da estrarre: {metrics_str}

Testo del documento (primi 8000 caratteri):
{pdf_text[:200]}...[TRONCATO]
                                    """
                                    st.code(prompt_preview, language="text")
                                    
                                    st.write("**Risposta completa dell'AI:**")
                                    if financial_response:
                                        st.text(financial_response)
                                    else:
                                        st.error("Nessuna risposta ricevuta")
                        
                        if financial_response:
                            financial_data = extract_json_from_response(financial_response)
                            
                            # Debug: Parsing JSON finanziario
                            if debug_mode:
                                with debug_container:
                                    with st.expander(f"💱 Debug JSON Parsing Finanziario: {company_name}", expanded=False):
                                        st.write("**JSON estratto:**")
                                        if financial_data:
                                            st.json(financial_data)
                                        else:
                                            st.error("Impossibile estrarre JSON valido dalla risposta")
                            
                            if financial_data:
                                # Memorizza risultati
                                if company_name not in results:
                                    results[company_name] = {}
                                
                                fiscal_year = company_info.get('fiscal_year', 'Sconosciuto')
                                results[company_name][fiscal_year] = {
                                    'company_info': company_info,
                                    'financial_data': financial_data,
                                    'source': pdf_source
                                }
                                
                                st.success(f"✅ Completato: {pdf_source['name']} - {company_name}")
                            else:
                                st.error(f"❌ Impossibile estrarre dati finanziari validi per {pdf_source['name']}")
                        else:
                            st.error(f"❌ Nessuna risposta dall'AI per l'estrazione finanziaria di {pdf_source['name']}")
                    else:
                        st.error(f"❌ Impossibile identificare l'azienda per {pdf_source['name']}")
                else:
                    st.error(f"❌ Nessuna risposta dall'AI per l'identificazione azienda di {pdf_source['name']}")
            else:
                st.error(f"❌ Impossibile estrarre testo significativo da {pdf_source['name']}")
                if pdf_text and debug_mode:
                    with debug_container:
                        with st.expander(f"⚠️ Debug Testo Insufficiente: {pdf_source['name']}", expanded=True):
                            st.write(f"**Testo estratto ({len(pdf_text)} caratteri):**")
                            st.text(pdf_text[:500] if pdf_text else "Nessun testo estratto")
            
            progress_bar.progress((i + 1) / total_docs)
        
        # Debug: Riepilogo finale
        if debug_mode:
            with debug_container:
                st.subheader("📊 Riepilogo Debug")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("📄 Documenti processati", total_docs)
                
                with col2:
                    successful_companies = len(results)
                    st.metric("🏢 Aziende identificate", successful_companies)
                
                with col3:
                    total_extractions = sum(len(years) for years in results.values())
                    st.metric("💰 Estrazioni completate", total_extractions)
                
                if results:
                    st.write("**Dettagli risultati:**")
                    for company, years_data in results.items():
                        st.write(f"- **{company}**: {len(years_data)} anni di dati")
                        for year in years_data.keys():
                            metrics_count = len(years_data[year]['financial_data'])
                            st.write(f"  - {year}: {metrics_count} metriche estratte")
        
        # Visualizza risultati
        if results:
            st.header("📊 Risultati Analisi")
            
            # Crea tab per ogni azienda
            company_names = list(results.keys())
            tabs = st.tabs(company_names)
            
            for tab, company_name in zip(tabs, company_names):
                with tab:
                    st.subheader(f"📈 {company_name}")
                    
                    # Ottieni anni per questa azienda
                    years_data = results[company_name]
                    years = sorted(years_data.keys())
                    
                    # Crea DataFrame per visualizzazione
                    df_data = []
                    for year in years:
                        row = {'Anno': year}
                        financial_data = years_data[year]['financial_data']
                        
                        for metric in selected_metrics:
                            if metric in financial_data:
                                value = financial_data[metric].get('value')
                                unit = financial_data[metric].get('unit', '')
                                row[metric] = f"{value} {unit}" if value else "N/D"
                            else:
                                row[metric] = "N/D"
                        
                        df_data.append(row)
                    
                    # Visualizza tabella
                    if df_data:
                        df = pd.DataFrame(df_data)
                        st.dataframe(df, use_container_width=True)
                        
                        # Crea grafici per metriche numeriche
                        numeric_data = []
                        for year in years:
                            row = {'Anno': int(year) if year.isdigit() else year}
                            financial_data = years_data[year]['financial_data']
                            
                            for metric in selected_metrics:
                                if metric in financial_data:
                                    value = financial_data[metric].get('value')
                                    if value and isinstance(value, (int, float)):
                                        row[metric] = value
                            
                            if len(row) > 1:  # Più del solo anno
                                numeric_data.append(row)
                        
                        # Disegna grafici se abbiamo dati numerici
                        if len(numeric_data) > 1:
                            df_numeric = pd.DataFrame(numeric_data)
                            
                            # Crea grafico a linee
                            fig = go.Figure()
                            
                            for metric in selected_metrics:
                                if metric in df_numeric.columns:
                                    fig.add_trace(go.Scatter(
                                        x=df_numeric['Anno'],
                                        y=df_numeric[metric],
                                        mode='lines+markers',
                                        name=metric,
                                        line=dict(width=3),
                                        marker=dict(size=8)
                                    ))
                            
                            fig.update_layout(
                                title=f"{company_name} - Trend Finanziari",
                                xaxis_title="Anno",
                                yaxis_title="Valore (Milioni)",
                                hovermode='x unified'
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                    
                    # Informazioni sulle fonti
                    st.write("**Fonti Documenti:**")
                    for year, data in years_data.items():
                        source_info = data['source']
                        st.write(f"- {year}: {source_info['name']} (caricato)")
            
            # Funzionalità di esportazione
            st.header("💾 Esporta Risultati")
            
            # Prepara dati per esportazione
            export_data = []
            for company_name, years_data in results.items():
                for year, data in years_data.items():
                    row = {
                        'Azienda': company_name,
                        'Anno': year,
                        'Valuta': data['company_info'].get('currency', 'Sconosciuta')
                    }
                    
                    financial_data = data['financial_data']
                    for metric in selected_metrics:
                        if metric in financial_data:
                            row[metric] = financial_data[metric].get('value')
                        else:
                            row[metric] = None
                    
                    export_data.append(row)
            
            if export_data:
                export_df = pd.DataFrame(export_data)
                
                # Pulsante di download
                csv = export_df.to_csv(index=False)
                st.download_button(
                    label="📥 Scarica Risultati come CSV",
                    data=csv,
                    file_name=f"analisi_finanziaria_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

elif pdf_sources and selected_metrics and not openrouter_api_key:
    st.warning("⚠️ Inserisci la tua chiave API OpenRouter nella barra laterale per procedere con l'analisi.")

elif pdf_sources and not selected_metrics:
    st.warning("⚠️ Seleziona almeno una metrica finanziaria da estrarre.")

# Sezione informativa
with st.expander("ℹ️ Come utilizzare l'applicazione"):
    st.markdown("""
    ### 🚀 Guida Rapida:
    
    1. **Configura API**: Inserisci la tua chiave API OpenRouter nella barra laterale
    2. **Scegli Modello**: Seleziona il modello AI che preferisci
    3. **Seleziona Metriche**: Scegli quali dati finanziari estrarre
    4. **Carica Documenti**: Upload dei file PDF
    5. **Analizza**: Clicca "Analizza Documenti Finanziari"
    6. **Visualizza**: Esplora i risultati per azienda
    7. **Esporta**: Scarica i dati in formato CSV
    
    ### 📋 Requisiti Documenti:
    - **Formato**: PDF di relazioni finanziarie, bilanci, report annuali
    - **Lingua**: Supporto per documenti in italiano e inglese
    - **Dimensione**: Consigliati file sotto i 50MB per performance ottimali
    
    ### 🔒 Privacy e Sicurezza:
    - Le chiavi API sono gestite localmente e non memorizzate
    - I documenti sono processati temporaneamente e non salvati
    - Tutti i dati rimangono privati durante l'analisi
    """)

# Footer
st.markdown("---")
st.markdown("📊 Financial PDF Analyzer")