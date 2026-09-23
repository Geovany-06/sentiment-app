import streamlit as st
import pandas as pd
import re

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
    rows = []
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
    counts = df["sentiment"].value_counts().reindex(
        ["positive", "negative", "neutral"], fill_value=0
    )
    chart_df = pd.DataFrame(
        {
            "Sentimiento": [t["positive"], t["negative"], t["neutral"]],
            "Cantidad": counts.values,
        }
    ).set_index("Sentimiento")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.bar_chart(chart_df, color="#4C78A8")
    with col2:
        st.markdown(f"**{t['summary_header']}**")
        st.metric(t["total"], len(df))
        st.metric(t["positive"], int(counts["positive"]))
        st.metric(t["negative"], int(counts["negative"]))
        st.metric(t["neutral"], int(counts["neutral"]))

    csv_bytes = df_display.to_csv(index=False).encode("utf-8")
    st.download_button(t["download"], data=csv_bytes, file_name="resultados_sentimiento.csv", mime="text/csv")
else:
    st.info(t["no_data"])
