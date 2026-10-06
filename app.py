import streamlit as st
import pandas as pd
import re
import json
import requests

# =========================================================
# CONFIGURACIÓN DE PÁGINA
# =========================================================
st.set_page_config(page_title="Analizador de Sentimiento", page_icon="💬", layout="wide")

# =========================================================
# LÉXICOS DE PALABRAS (positivas / negativas) ES e EN
# =========================================================
LEXICON = {
    "Español": {
        "pos": {
            "bueno", "buena", "excelente", "genial", "increible", "increíble", "feliz",
            "mejor", "fantastico", "fantástico", "perfecto", "perfecta", "maravilloso",
            "maravillosa", "recomiendo", "satisfecho", "satisfecha", "calidad", "rapido",
            "rápido", "facil", "fácil", "encanta", "encantado", "encantada", "amable",
            "amo", "contento", "contenta", "agradable", "impresionante", "eficiente",
            "gracias", "util", "útil", "bien", "super", "súper", "positivo", "positiva",
            "recomendable", "exitoso", "exitosa", "comodo", "cómodo", "comoda", "cómoda"
        },
        "neg": {
            "malo", "mala", "terrible", "peor", "odio", "horrible", "pobre", "lento",
            "lenta", "decepcionante", "problema", "problemas", "dificil", "difícil",
            "caro", "cara", "nunca", "pesimo", "pésimo", "pesima", "pésima", "roto",
            "rota", "defectuoso", "defectuosa", "queja", "molesto", "molesta", "triste",
            "enojado", "enojada", "fallo", "falla", "fallos", "decepcionado",
            "decepcionada", "mal", "negativo", "negativa", "estafa", "lamentable",
            "insatisfecho", "insatisfecha", "no funciona", "no recomiendo"
        },
    },
    "English": {
        "pos": {
            "good", "great", "excellent", "love", "amazing", "happy", "best", "awesome",
            "perfect", "wonderful", "nice", "fantastic", "recommend", "satisfied",
            "quality", "fast", "easy", "helpful", "friendly", "impressive", "efficient",
            "thanks", "useful", "well", "super", "positive", "recommended", "successful",
            "comfortable", "pleased", "delighted", "outstanding"
        },
        "neg": {
            "bad", "terrible", "worst", "hate", "awful", "poor", "slow", "disappointing",
            "problem", "problems", "difficult", "expensive", "never", "horrible", "broken",
            "defective", "complaint", "annoying", "sad", "angry", "fail", "failure",
            "disappointed", "negative", "scam", "unfortunate", "unsatisfied", "not working",
            "do not recommend", "don't recommend"
        },
    },
}

TEXT = {
    "Español": {
        "title": "💬 Analizador de Sentimiento de Comentarios",
        "subtitle": "Sube un archivo o usa el conjunto de datos interno. Clasifica cada comentario como Positivo, Negativo o Neutral.",
        "lang_label": "Idioma de análisis",
        "upload_label": "Sube un archivo (.csv o .txt) con los comentarios",
        "upload_help": "Si subes un .csv, indica la columna que contiene el texto. Si subes .txt, cada línea se toma como un comentario.",
        "use_sample": "Usar conjunto de comentarios interno (ejemplo)",
        "column_select": "Selecciona la columna con los comentarios",
        "results_header": "📋 Resultados del análisis",
        "chart_header": "📊 Distribución de sentimientos",
        "summary_header": "Resumen",
        "positive": "Positivo",
        "negative": "Negativo",
        "neutral": "Neutral",
        "download": "⬇️ Descargar resultados en CSV",
        "no_data": "Sube un archivo o activa el conjunto interno para ver resultados.",
        "comment_col": "Comentario",
        "sentiment_col": "Sentimiento",
        "score_col": "Puntaje",
        "total": "Total de comentarios",
    },
    "English": {
        "title": "💬 Comment Sentiment Analyzer",
        "subtitle": "Upload a file or use the built-in dataset. Classifies each comment as Positive, Negative or Neutral.",
        "lang_label": "Analysis language",
        "upload_label": "Upload a file (.csv or .txt) with the comments",
        "upload_help": "If you upload a .csv, choose the column that holds the text. If you upload .txt, each line is treated as one comment.",
        "use_sample": "Use built-in sample comment set",
        "column_select": "Select the column with the comments",
        "results_header": "📋 Analysis results",
        "chart_header": "📊 Sentiment distribution",
        "summary_header": "Summary",
        "positive": "Positive",
        "negative": "Negative",
        "neutral": "Neutral",
        "download": "⬇️ Download results as CSV",
        "no_data": "Upload a file or enable the built-in dataset to see results.",
        "comment_col": "Comment",
        "sentiment_col": "Sentiment",
        "score_col": "Score",
        "total": "Total comments",
    },
}

# Conjunto interno de comentarios de ejemplo (mixto ES/EN funciona bien con ambos léxicos)
SAMPLE_COMMENTS = {
    "Español": [
        "El producto es excelente, llegó rápido y la calidad es increíble.",
        "Muy mal servicio, el pedido llegó roto y nadie responde.",
        "Estoy satisfecho con la compra, lo recomiendo totalmente.",
        "Terrible experiencia, no recomiendo esta tienda para nada.",
        "El envío fue normal, sin problemas destacables.",
        "Me encanta este producto, es perfecto y muy cómodo.",
        "Pésima atención al cliente, una estafa total.",
        "Todo bien, cumple lo que promete.",
        "El precio es un poco caro pero la calidad es buena.",
        "No funciona como esperaba, estoy decepcionado.",
    ],
    "English": [
        "The product is excellent, arrived fast and the quality is amazing.",
        "Very bad service, the order arrived broken and nobody responds.",
        "I'm satisfied with the purchase, I totally recommend it.",
        "Terrible experience, I do not recommend this store at all.",
        "The shipping was normal, no notable problems.",
        "I love this product, it's perfect and very comfortable.",
        "Awful customer service, a total scam.",
        "Everything is fine, it delivers what it promises.",
        "The price is a bit expensive but the quality is good.",
        "It doesn't work as expected, I'm disappointed.",
    ],
}


# =========================================================
# FUNCIONES DE ANÁLISIS
# =========================================================
def clean_tokens(text: str):
    text = str(text).lower()
    text = re.sub(r"[^a-záéíóúñü\s]", " ", text)
    return text.split()


def analyze_sentiment(text: str, lang: str):
    words = clean_tokens(text)
    text_lower = str(text).lower()
    pos_set = LEXICON[lang]["pos"]
    neg_set = LEXICON[lang]["neg"]

    pos_hits = sum(1 for w in words if w in pos_set)
    neg_hits = sum(1 for w in words if w in neg_set)

    # frases negativas de dos palabras (ej. "no funciona", "not working")
    for phrase in pos_set:
        if " " in phrase and phrase in text_lower:
            pos_hits += 1
    for phrase in neg_set:
        if " " in phrase and phrase in text_lower:
            neg_hits += 1

    score = pos_hits - neg_hits
    if score > 0:
        sentiment = "positive"
    elif score < 0:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    return sentiment, score


# =========================================================
# ANÁLISIS CON IA (Google Gemini API)
# =========================================================
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)


def analyze_sentiment_gemini(text: str, lang: str, api_key: str):
    """Clasifica un comentario llamando a la API de Google Gemini.
    Devuelve (sentiment, score) igual que analyze_sentiment, para que
    el resto de la app no tenga que cambiar."""
    if lang == "Español":
        prompt = (
            "Clasifica el sentimiento del siguiente comentario como "
            "exactamente una de estas tres palabras: positivo, negativo o neutral. "
            "Responde SOLO con esa palabra, sin explicaciones.\n\n"
            f"Comentario: \"{text}\""
        )
    else:
        prompt = (
            "Classify the sentiment of the following comment as exactly one "
            "of these three words: positive, negative or neutral. "
            "Reply with ONLY that word, no explanations.\n\n"
            f"Comment: \"{text}\""
        )

    try:
        response = requests.post(
            f"{GEMINI_URL}?key={api_key}",
            headers={"Content-Type": "application/json"},
            data=json.dumps(
                {"contents": [{"parts": [{"text": prompt}]}]}
            ),
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        raw = data["candidates"][0]["content"]["parts"][0]["text"].strip().lower()
    except Exception as e:
        # Si la API falla (sin internet, clave inválida, límite alcanzado, etc.)
        # se cae de vuelta al método de palabras clave para no romper la app.
        return analyze_sentiment(text, lang)

    if "posit" in raw:
        sentiment, score = "positive", 1
    elif "negat" in raw:
        sentiment, score = "negative", -1
    else:
        sentiment, score = "neutral", 0
    return sentiment, score


# =========================================================
# INTERFAZ
# =========================================================
lang = st.sidebar.radio("Idioma / Language", ["Español", "English"], index=0)
t = TEXT[lang]

st.title(t["title"])
st.caption(t["subtitle"])

st.sidebar.markdown("---")
use_sample = st.sidebar.checkbox(t["use_sample"], value=True)
uploaded_file = st.sidebar.file_uploader(
    t["upload_label"], type=["csv", "txt"], help=t["upload_help"]
)

st.sidebar.markdown("---")
method_label = "Método de análisis" if lang == "Español" else "Analysis method"
method_keywords = "Palabras clave (rápido, sin internet)" if lang == "Español" else "Keywords (fast, no internet)"
method_ai = "IA - Google Gemini (requiere API key)" if lang == "Español" else "AI - Google Gemini (requires API key)"
method = st.sidebar.radio(method_label, [method_keywords, method_ai])

api_key = ""
if method == method_ai:
    api_key_label = "Tu API key de Gemini" if lang == "Español" else "Your Gemini API key"
    api_key_help = (
        "Consíguela gratis en aistudio.google.com/apikey"
        if lang == "Español"
        else "Get one for free at aistudio.google.com/apikey"
    )
    api_key = st.sidebar.text_input(api_key_label, type="password", help=api_key_help)
    if not api_key:
        warn_msg = (
            "Pega tu API key para usar este método. Mientras tanto, se usará el método de palabras clave."
            if lang == "Español"
            else "Paste your API key to use this method. Using keyword method for now."
        )
        st.sidebar.warning(warn_msg)

comments = []

if uploaded_file is not None:
    if uploaded_file.name.endswith(".csv"):
        df_raw = pd.read_csv(uploaded_file)
        col = st.sidebar.selectbox(t["column_select"], df_raw.columns)
        comments = df_raw[col].dropna().astype(str).tolist()
    else:  # .txt
        content = uploaded_file.read().decode("utf-8", errors="ignore")
        comments = [line.strip() for line in content.splitlines() if line.strip()]
elif use_sample:
    comments = SAMPLE_COMMENTS[lang]

# =========================================================
# PROCESAMIENTO Y RESULTADOS
# =========================================================
if comments:
    use_ai = (method == method_ai) and bool(api_key)
    rows = []

    if use_ai:
        progress_label = "Analizando con IA..." if lang == "Español" else "Analyzing with AI..."
        progress_bar = st.progress(0, text=progress_label)
        for i, c in enumerate(comments):
            sentiment, score = analyze_sentiment_gemini(c, lang, api_key)
            rows.append({"comment": c, "sentiment": sentiment, "score": score})
            progress_bar.progress((i + 1) / len(comments), text=progress_label)
        progress_bar.empty()
        method_used_msg = (
            "✅ Resultados generados con IA (Google Gemini)."
            if lang == "Español"
            else "✅ Results generated using AI (Google Gemini)."
        )
        st.success(method_used_msg)
    else:
        for c in comments:
            sentiment, score = analyze_sentiment(c, lang)
            rows.append({"comment": c, "sentiment": sentiment, "score": score})

    df = pd.DataFrame(rows)

    label_map = {
        "positive": t["positive"],
        "negative": t["negative"],
        "neutral": t["neutral"],
    }
    df_display = df.rename(
        columns={
            "comment": t["comment_col"],
            "sentiment": t["sentiment_col"],
            "score": t["score_col"],
        }
    )
    df_display[t["sentiment_col"]] = df_display[t["sentiment_col"]].map(label_map)

    st.subheader(t["results_header"])
    st.dataframe(df_display, use_container_width=True)

    st.subheader(t["chart_header"])
    total_comments = len(df)
    counts = df["sentiment"].value_counts().reindex(
        ["positive", "negative", "neutral"], fill_value=0
    )
    percentages = (counts / total_comments * 100).round(1)

    chart_df = pd.DataFrame(
        {
            "Sentimiento": [t["positive"], t["negative"], t["neutral"]],
            "Cantidad": counts.values,
            "Porcentaje": percentages.values,
        }
    ).set_index("Sentimiento")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.bar_chart(chart_df[["Cantidad"]], color="#4C78A8")
    with col2:
        st.markdown(f"**{t['summary_header']}**")
        st.metric(t["total"], total_comments)
        st.metric(
            t["positive"],
            int(counts["positive"]),
            delta=f"{percentages['positive']}%",
            delta_color="off",
        )
        st.metric(
            t["negative"],
            int(counts["negative"]),
            delta=f"{percentages['negative']}%",
            delta_color="off",
        )
        st.metric(
            t["neutral"],
            int(counts["neutral"]),
            delta=f"{percentages['neutral']}%",
            delta_color="off",
        )

    # Tabla con el detalle de cantidades y porcentajes por categoría
    pct_table_title = (
        "📈 Porcentaje de comentarios por categoría"
        if lang == "Español"
        else "📈 Percentage of comments by category"
    )
    st.markdown(f"**{pct_table_title}**")
    pct_display = chart_df.reset_index().rename(
        columns={"Porcentaje": "Porcentaje (%)" if lang == "Español" else "Percentage (%)"}
    )
    st.dataframe(pct_display, use_container_width=True, hide_index=True)

    csv_bytes = df_display.to_csv(index=False).encode("utf-8")
    st.download_button(t["download"], data=csv_bytes, file_name="resultados_sentimiento.csv", mime="text/csv")
else:
    st.info(t["no_data"])
