import streamlit as st
import requests
import json
import time
import pandas as pd
from datetime import datetime
from urllib.parse import quote_plus

def get_search_type_params(search_type):
    """
    Restituisce i parametri base e i campi da estrarre per ogni tipo di ricerca
    """
    search_types = {
        "web": {
            "params": {},
            "results_key": "organic_results",
            "export_fields": ["title", "link", "snippet", "displayed_link", "position"]
        },
        "images": {
            "params": {"tbm": "isch"},
            "results_key": "images_results", 
            "export_fields": ["original"]
        },
        "news": {
            "params": {"tbm": "nws"},
            "results_key": "news_results",
            "export_fields": ["title", "link", "snippet", "source", "date", "position"]
        },
        "videos": {
            "params": {"tbm": "vid"},
            "results_key": "video_results",
            "export_fields": ["title", "link", "platform", "duration", "position"]
        },
        "shopping": {
            "params": {"tbm": "shop"},
            "results_key": "shopping_results",
            "export_fields": ["title", "link", "price", "source", "rating", "reviews", "position"]
        }
    }
    return search_types.get(search_type, search_types["web"])

def build_query(base_query, domain=None, directory_include=None, directory_exclude=None, exclude_sites=None, 
                exact_phrase=None, exclude_words=None, filetype=None, exclude_filetypes=None, date_after=None, date_before=None):
    """
    Costruisce la query di ricerca completa con supporto per domini, directory e vari filtri
    """
    query_parts = []
    
    # Aggiungi query base
    if base_query:
        query_parts.append(base_query)
    
    # Aggiungi frase esatta
    if exact_phrase:
        query_parts.append(f'"{exact_phrase}"')
    
    # Aggiungi dominio principale
    if domain:
        query_parts.append(f'site:{domain}')
    
    # Aggiungi directory da includere
    if directory_include:
        query_parts.append(f'inurl:{directory_include}')
    
    # Aggiungi directory da escludere
    if directory_exclude:
        query_parts.append(f'-inurl:{directory_exclude}')
    
    # Aggiungi siti/sottodomini da escludere
    if exclude_sites:
        for site in exclude_sites.split(','):
            site = site.strip()
            if site:
                query_parts.append(f'-site:{site}')
    
    # Aggiungi parole da escludere
    if exclude_words:
        for word in exclude_words.split(','):
            word = word.strip()
            if word:
                query_parts.append(f'-{word}')
    
    # Aggiungi tipo di file
    if filetype:
        query_parts.append(f'filetype:{filetype}')
    
    # Aggiungi tipi di file da escludere (multipli)
    if exclude_filetypes:
        for exclude_type in exclude_filetypes:
            query_parts.append(f'-filetype:{exclude_type}')
    
    # Aggiungi date
    if date_after:
        query_parts.append(f'after:{date_after}')
    if date_before:
        query_parts.append(f'before:{date_before}')
    
    return ' '.join(query_parts)

class SerpApiClient:
    SEARCH_TYPES = {
        "web": "Web",
        "images": "Immagini", 
        "news": "Notizie",
        "videos": "Video",
        "shopping": "Shopping"
    }

    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://serpapi.com/search"

    def search(self, query, search_type="web", params=None):
        """
        Esegue una ricerca usando SerpApi
        """
        search_type_info = get_search_type_params(search_type)
        default_params = {
            "engine": "google",
            "google_domain": "google.com",
            "gl": "it",
            "hl": "it", 
            "num": 100,
            "api_key": self.api_key,
            "q": query
        }
        
        # Aggiungi i parametri specifici del tipo di ricerca
        default_params.update(search_type_info["params"])
        
        if params:
            default_params.update(params)
            
        try:
            response = requests.get(self.base_url, params=default_params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Errore nella richiesta: {str(e)}")
            return None

    def get_results(self, query, search_type="web", max_pages=10, params=None):
        """
        Recupera tutti i risultati disponibili con paginazione
        """
        all_results = []
        current_page = 0
        search_type_info = get_search_type_params(search_type)
        results_key = search_type_info["results_key"]
        
        with st.spinner(f"Recupero risultati {self.SEARCH_TYPES[search_type]}..."):
            progress_bar = st.progress(0)
            
            while current_page < max_pages:
                progress_bar.progress(current_page / max_pages)
                
                page_params = params.copy() if params else {}
                page_params["start"] = current_page * 100
                
                results = self.search(query, search_type, page_params)
                
                if not results or "error" in results:
                    break
                    
                results_list = results.get(results_key, [])
                
                # Filtra i risultati per le immagini
                if search_type == "images":
                    results_list = [
                        result for result in results_list 
                        if result.get('original') 
                        and result['original'].strip() != ""
                        and not result['original'].startswith('x-raw-image:///')
                    ]
                
                if not results_list:
                    break
                    
                all_results.extend(results_list)
                
                if "serpapi_pagination" not in results or "next" not in results["serpapi_pagination"]:
                    break
                    
                current_page += 1
                time.sleep(1)  # Rate limiting
            
            progress_bar.progress(1.0)
            
            # Mostra info sui risultati filtrati per le immagini
            if search_type == "images":
                total_results = len(results.get(results_key, []))
                filtered_results = len(all_results)
                if total_results != filtered_results:
                    st.info(f"Filtrati {total_results - filtered_results} risultati non validi o vuoti")
                
        return all_results

def create_serp_interface():
    st.title("🔍 Google Search Extractor")
    
    # Configurazione nella sidebar
    with st.sidebar:
        st.header("⚙️ Configurazione")
        
        use_secrets = st.checkbox("Usa credenziali salvate", value=True)
        
        api_key = None
        if use_secrets:
            try:
                api_key = st.secrets["serp_api"]["api_key"]
                st.success("✅ Credenziali caricate dai secrets")
            except Exception:
                st.error("❌ Errore nel caricamento dei secrets")
                use_secrets = False
                
        if not use_secrets:
            api_key = st.text_input(
                "SerpApi Key",
                type="password",
                help="Inserisci la tua chiave API di SerpApi"
            )

    # Parametri di localizzazione
    params = {
        "gl": "it",
        "hl": "it"
    }
    
    with st.form("search_form"):
        st.subheader("🎯 Parametri di ricerca")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            base_query = st.text_input(
                "Query base",
                help="Inserisci la query base della ricerca"
            )
            
            exact_phrase = st.text_input(
                "Query esatta",
                help="La frase o parola verrà cercata esattamente come scritta"
            )
            
            domain = st.text_input(
                "Dominio da cercare",
                help="es: example.com"
            )

            directory_include = st.text_input(
                "Directory da includere",
                help="es: /blog/ (cerca solo in questa directory)"
            )
            
            directory_exclude = st.text_input(
                "Directory da escludere",
                help="es: /en/ (esclude questa directory dalla ricerca)"
            )
            
            exclude_sites = st.text_input(
                "Domini da escludere (separati da virgola)",
                help="es: shop.example.com, otherdomain.com"
            )

            exclude_words = st.text_input(
                "Parole da escludere (separate da virgola)",
                help="es: spam, ads"
            )

        with col2:
            search_type = st.selectbox(
                "Tipo di ricerca",
                options=list(SerpApiClient.SEARCH_TYPES.keys()),
                format_func=lambda x: SerpApiClient.SEARCH_TYPES[x]
            )
            
            with st.expander("⚙️ Opzioni avanzate", expanded=False):
                # File types
                st.markdown("##### Filtri file")
                filetype_col1, filetype_col2 = st.columns(2)
                
                with filetype_col1:
                    filetype = st.selectbox(
                        "Includi file",
                        options=["", "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx"],
                        format_func=lambda x: f".{x}" if x else "Qualsiasi"
                    )
                
                with filetype_col2:
                    exclude_filetypes = st.multiselect(
                        "Escludi file",
                        options=["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx"],
                        format_func=lambda x: f".{x}",
                        help="Seleziona uno o più tipi di file da escludere"
                    )
                
                # Date filters
                st.markdown("##### Filtri data")
                date_col1, date_col2 = st.columns(2)
                
                with date_col1:
                    date_after = st.date_input(
                        "Data dopo",
                        value=None,
                        help="Risultati dopo questa data"
                    )
                
                with date_col2:
                    date_before = st.date_input(
                        "Data prima",
                        value=None,
                        help="Risultati prima di questa data"
                    )
            
            max_pages = st.number_input(
                "Numero max pagine",
                min_value=1,
                max_value=10,
                value=1,
                help="Massimo numero di pagine da recuperare (100 risultati per pagina)"
            )
        
        # Costruisci e mostra la query
        query = build_query(
            base_query=base_query,
            domain=domain,
            directory_include=directory_include,
            directory_exclude=directory_exclude,
            exclude_sites=exclude_sites,
            exact_phrase=exact_phrase,
            exclude_words=exclude_words,
            filetype=filetype,
            exclude_filetypes=exclude_filetypes,
            date_after=date_after.strftime("%Y-%m-%d") if date_after else None,
            date_before=date_before.strftime("%Y-%m-%d") if date_before else None
        )
        
        if query:
            st.code(query, language="text")
            
        submitted = st.form_submit_button("🔍 Avvia ricerca")

        if submitted:
            if not query:
                st.warning("⚠️ Inserisci almeno un parametro di ricerca!")
                return
                
            if not api_key:
                st.error("⚠️ Inserisci una chiave API!")
                return
                
            # Inizializza il client
            client = SerpApiClient(api_key)
            
            # Esegui la ricerca
            try:
                results = client.get_results(query, search_type, max_pages, params)
                
                if results:
                    st.session_state['search_results'] = results
                    st.session_state['search_type'] = search_type
                    st.session_state['export_fields'] = get_search_type_params(search_type)["export_fields"]
            except Exception as e:
                st.error(f"❌ Errore durante la ricerca: {str(e)}")
                return

    # Mostra risultati se presenti in session state
    if 'search_results' in st.session_state:
        results = st.session_state['search_results']
        search_type = st.session_state['search_type']
        export_fields = st.session_state['export_fields']
        
        df = pd.DataFrame(results)
        
        # Visualizzazione risultati
        st.subheader("📊 Risultati della ricerca")
        
        # Metriche
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Totale risultati", len(results))
        with col2:
            st.metric("Pagine recuperate", max_pages)
        
        # Visualizza risultati in tabella
        if all(field in df.columns for field in export_fields):
            export_df = df[export_fields].copy()
            st.dataframe(export_df, use_container_width=True)
            
            # Download buttons
            st.subheader("📥 Esporta risultati")
            col1, col2 = st.columns(2)
            
            # JSON con metadati completi
            with col1:
                json_data = {
                    "query": query,
                    "search_type": search_type,
                    "timestamp": datetime.now().isoformat(),
                    "total_results": len(results),
                    "pages_retrieved": max_pages,
                    "parameters": params,
                    "results": json.loads(df.to_json(orient="records"))
                }
                
                json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
                
                st.download_button(
                    label="📥 Scarica JSON",
                    data=json_str.encode('utf-8'),
                    file_name=f"search_results_{search_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            with col2:
                csv_buffer = df[export_fields].to_csv(index=False)
                st.download_button(
                    label="📥 Scarica CSV",
                    data=csv_buffer,
                    file_name=f"search_results_{search_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        else:
            st.error("❌ I risultati non contengono i campi attesi")
            return

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center'>
            <p>Sviluppato con ❤️ usando Streamlit</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    # Configurazione della pagina Streamlit
    st.set_page_config(
        page_title="Google Search Extractor",
        page_icon="🔍",
        layout="wide"
    )
    create_serp_interface()
