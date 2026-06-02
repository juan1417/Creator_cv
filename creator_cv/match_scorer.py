"""Quantitative match scoring between a CV and a job offer.

Provides a fast, deterministic local scorer that returns a 0-100 score
plus a per-dimension breakdown. Used for the badge shown in the
dashboard list and for the inline analysis popup.

Scoring (default weights, sum to 100):

* **Tecnicas** (60 pts): how many of the offer's required technical
  keywords appear in the CV's technical skills / experience / projects.
* **Idiomas** (20 pts): how many of the offer's required languages
  appear in the CV's language list (with level hint when possible).
* **Experiencia** (20 pts): rough heuristic — the CV's total years
  of experience vs. an inferred "required" seniority from the offer.

Keyword extraction is deliberately lightweight: tokenize the offer,
lowercase, strip punctuation, drop stopwords, and keep nouns/noun
phrases that match a small dictionary of common tech terms (and
anything >= 3 chars that isn't a stopword). It's a heuristic — good
enough for a quick badge, not a substitute for an ATS.
"""

from __future__ import annotations

import re
from typing import Any


# --- Stopwords (es + en) ------------------------------------------------

_STOPWORDS: set[str] = {
    # ES
    "a", "al", "algo", "algunas", "algunos", "ante", "antes", "como", "con",
    "contra", "cual", "cuando", "de", "del", "desde", "donde", "durante",
    "e", "el", "ella", "ellas", "ellos", "en", "entre", "era", "erais",
    "eran", "eras", "eres", "es", "esa", "esas", "ese", "eso", "esos",
    "esta", "estaba", "estabais", "estaban", "estabas", "estad", "estada",
    "estadas", "estado", "estados", "estais", "estamos", "estan", "estar",
    "estará", "estarán", "estarás", "estaré", "estaréis", "estaríamos",
    "estarían", "estarías", "estas", "este", "esto", "estos", "estoy",
    "estuve", "estuviera", "estuvierais", "estuvieran", "estuvieras",
    "estuvieron", "estuviese", "estuvieseis", "estuviesen", "estuvieses",
    "estuvimos", "estuviste", "estuvisteis", "estuvo", "etc", "fue",
    "fuera", "fuerais", "fueran", "fueras", "fueron", "fuese", "fueseis",
    "fuesen", "fueses", "fui", "fuimos", "fuiste", "fuisteis", "ha", "habeis",
    "haber", "habida", "habidas", "habido", "habidos", "habiendo",
    "habrá", "habrán", "había", "habíamos", "habían", "habías", "han",
    "has", "hasta", "hay", "hayas", "he", "hemos", "hube", "hubiera",
    "hubierais", "hubieran", "hubieras", "hubieron", "hubiese", "hubieseis",
    "hubiesen", "hubieses", "hubimos", "hubiste", "hubisteis", "hubo", "la",
    "las", "le", "les", "lo", "los", "más", "me", "mi", "mis", "mucho",
    "muchos", "muy", "nada", "ni", "no", "nos", "nosotras", "nosotros",
    "nuestra", "nuestras", "nuestro", "nuestros", "o", "os", "otra",
    "otras", "otro", "otros", "para", "pero", "poco", "por", "porque",
    "que", "quien", "quienes", "se", "sea", "seais", "seamos", "sean",
    "seas", "sentid", "sentida", "sentidas", "sentido", "sentidos", "sera",
    "será", "serán", "serás", "seré", "seréis", "seríamos", "serían",
    "serías", "siente", "sin", "sobre", "sois", "somos", "son", "soy",
    "su", "sus", "suya", "suyas", "suyo", "suyos", "también", "tanto",
    "te", "tendrá", "tendrán", "tendrás", "tendré", "tendríamos",
    "tendrían", "tendrías", "tened", "teneis", "tenemos", "tenga",
    "tengamos", "tengan", "tengas", "tengo", "tenida", "tenidas", "tenido",
    "tenidos", "teniendo", "tenía", "teníamos", "tenían", "tenías", "ti",
    "tiene", "tienen", "tienes", "todo", "todos", "tu", "tus", "tuya",
    "tuyas", "tuyo", "tuyos", "un", "una", "uno", "unos", "vosotras",
    "vosotros", "vuestra", "vuestras", "vuestro", "vuestros", "y", "ya",
    "yo",
    # EN
    "a", "about", "above", "after", "again", "against", "all", "am", "an",
    "and", "any", "are", "as", "at", "be", "because", "been", "before",
    "being", "below", "between", "both", "but", "by", "could", "did",
    "do", "does", "doing", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers",
    "herself", "him", "himself", "his", "how", "i", "if", "in", "into",
    "is", "it", "its", "itself", "just", "me", "more", "most", "my",
    "myself", "no", "nor", "not", "now", "of", "off", "on", "once", "only",
    "or", "other", "our", "ours", "ourselves", "out", "over", "own", "same",
    "she", "should", "so", "some", "such", "than", "that", "the", "their",
    "theirs", "them", "themselves", "then", "there", "these", "they",
    "this", "those", "through", "to", "too", "under", "until", "up", "very",
    "was", "we", "were", "what", "when", "where", "which", "while", "who",
    "whom", "why", "will", "with", "would", "you", "your", "yours",
    "yourself", "yourselves",
}


# --- Lightweight "known tech" dictionary --------------------------------
# Used both to *find* tech terms in the offer and to recognise them
# in the CV even when written with a different casing or separator.

_KNOWN_TECH: set[str] = {
    # Lenguajes
    "python", "java", "javascript", "typescript", "go", "golang", "rust",
    "c", "c++", "c#", "csharp", "ruby", "php", "kotlin", "swift",
    "scala", "r", "matlab", "perl", "dart", "elixir", "haskell", "lua",
    # Frontend
    "react", "vue", "angular", "svelte", "next", "nextjs", "nuxt",
    "redux", "tailwind", "bootstrap", "sass", "scss", "webpack", "vite",
    "html", "css", "jquery",
    # Backend
    "flask", "django", "fastapi", "express", "nestjs", "spring", "springboot",
    "rails", "laravel", "symfony", "gin", "fiber", "node", "nodejs",
    "deno", "bun",
    # Móvil
    "ios", "android", "react-native", "flutter", "xamarin", "ionic",
    # Datos / DB
    "sql", "nosql", "postgresql", "postgres", "mysql", "mariadb",
    "mongodb", "redis", "cassandra", "dynamodb", "sqlite", "oracle",
    "elasticsearch", "neo4j", "clickhouse", "snowflake", "bigquery",
    # Data eng / ML
    "spark", "hadoop", "kafka", "airflow", "dbt", "etl", "elt",
    "pandas", "numpy", "scipy", "scikit-learn", "sklearn", "pytorch",
    "tensorflow", "keras", "jax", "huggingface", "transformers",
    "llm", "llms", "rag", "openai", "gemini", "claude", "embedding",
    "embeddings", "vector", "vectorstore", "langchain", "llamaindex",
    "mlops", "ml", "ai", "nlp", "computer-vision", "cv",
    # Cloud / DevOps
    "aws", "azure", "gcp", "google-cloud", "kubernetes", "k8s",
    "docker", "terraform", "ansible", "helm", "jenkins", "github-actions",
    "gitlab", "ci", "cd", "ci/cd", "argo", "istio", "prometheus",
    "grafana", "datadog", "elk", "splunk", "linux", "bash", "powershell",
    # Testing
    "pytest", "junit", "selenium", "cypress", "playwright", "jest",
    "mocha", "postman",
    # Metodologías / misc
    "agile", "scrum", "kanban", "tdd", "bdd", "rest", "graphql", "grpc",
    "soap", "kafka", "rabbitmq", "oauth", "jwt", "saml", "openid",
    "microservicios", "monolith", "serverless", "lambda",
    "machine-learning", "deep-learning", "data-science",
}


# Spanish normalisation map (offer/CV may use ES synonyms)
_ES_SYNONYMS: dict[str, str] = {
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "postgrés": "postgres",
    "postgres": "postgresql",
    "spring-boot": "spring",
    "spring_boot": "spring",
    "vuejs": "vue",
    "reactjs": "react",
    "node": "nodejs",
    "node-js": "nodejs",
    "node.js": "nodejs",
    "next.js": "nextjs",
    "ci-cd": "ci/cd",
    "ml": "machine-learning",
    "ia": "ai",
    "bbdd": "sql",
    "base-de-datos": "sql",
    "nube": "aws",
}


# --- Tokenization -------------------------------------------------------

_TOKEN_RE = re.compile(r"[A-Za-zÁÉÍÓÚáéíóúÑñÜü][A-Za-z0-9ÁÉÍÓÚáéíóúÑñÜü+#./-]*")
_YEARS_RE = re.compile(r"(\d+)\s*\+?\s*(años|years|yrs|year)\b", re.IGNORECASE)


def _norm(token: str) -> str:
    t = token.strip().lower()
    t = t.rstrip(".,;:()[]{}¡!¿?")
    return _ES_SYNONYMS.get(t, t)


def _tokenize(text: str) -> list[str]:
    return [_norm(m.group(0)) for m in _TOKEN_RE.finditer(text or "")]


def _is_stopword(t: str) -> bool:
    return t in _STOPWORDS or len(t) < 2


# --- Keyword extraction -------------------------------------------------


def extract_keywords(text: str) -> list[str]:
    """Return a deduplicated list of "interesting" tokens from ``text``.

    Strategy: keep tokens that are in :data:`_KNOWN_TECH`, plus
    alphanumeric tokens longer than 3 chars that aren't stopwords.
    """
    seen: set[str] = set()
    out: list[str] = []
    for tok in _tokenize(text):
        if not tok or _is_stopword(tok):
            continue
        if tok in _KNOWN_TECH or len(tok) >= 4:
            if tok not in seen:
                seen.add(tok)
                out.append(tok)
    return out


# --- Required-skill extraction from the offer ---------------------------


# Phrases that introduce "required" skills in offers.
_REQUIRED_HINTS = re.compile(
    r"\b(requerido|requeridos|requerida|requerim(iento|ientos)|"
    r"imprescindible|indispensable|necesario|necesaria|"
    r"must[- ]?have|required|requirements?|"
    r"experiencia en|conocimientos en|manejo de|"
    r"se requiere|se necesita|se valorará|valorable|"
    r"years of experience|experiência em)\b",
    re.IGNORECASE,
)


def _extract_tech_requirements(offer: str) -> list[str]:
    """Extract the technical requirements from a job offer.

    Strategy: take all tokens and prefer those in :data:`_KNOWN_TECH`.
    If we found at least 2 known techs, use only those. Otherwise, fall
    back to the most "tech-like" tokens (alphanumeric with no accents,
    length >= 5) — this avoids picking up Spanish/English stopwords or
    narrative words from a short offer.
    """
    keywords = extract_keywords(offer)
    known = sorted({k for k in keywords if k in _KNOWN_TECH})
    if len(known) >= 2:
        return known
    # Fallback: longer, alphanumeric tokens that look like tech terms.
    fallback = sorted(
        {
            k
            for k in keywords
            if k not in _STOPWORDS and len(k) >= 5 and k.replace("-", "").isalnum()
        }
    )
    return fallback


# --- Language parsing ---------------------------------------------------


_KNOWN_LANGS: dict[str, list[str]] = {
    "español": ["espanol", "español", "castellano", "spanish"],
    "inglés": ["ingles", "inglés", "english"],
    "francés": ["frances", "francés", "french"],
    "alemán": ["aleman", "alemán", "german"],
    "italiano": ["italian", "italiano"],
    "portugués": ["portugues", "portugués", "portuguese"],
    "catalán": ["catalan", "catalán"],
    "chino": ["chino", "chinese", "mandarin", "mandarín"],
    "japonés": ["japones", "japonés", "japanese"],
}


def _extract_required_languages(offer: str) -> list[str]:
    """Look for the typical 'idioma' / 'language' patterns in the offer."""
    text = (offer or "").lower()
    found: list[str] = []
    for canonical, variants in _KNOWN_LANGS.items():
        for v in variants:
            if re.search(rf"\b{re.escape(v)}\b", text):
                if canonical not in found:
                    found.append(canonical)
                break
    return found


def _cv_languages(cv: dict[str, Any]) -> set[str]:
    langs: set[str] = set()
    for raw in (cv.get("habilidades") or {}).get("idiomas") or []:
        s = _norm(str(raw))
        for canonical, variants in _KNOWN_LANGS.items():
            if any(v in s for v in variants):
                langs.add(canonical)
                break
        else:
            langs.add(s)
    return langs


# --- Experience years ---------------------------------------------------


def _cv_years(cv: dict[str, Any]) -> int:
    """Rough estimate of total years of experience from experiencia[].fecha_inicio/fin.

    Caps each item at 8 years to avoid weird outliers (e.g. a typo'd 2010).
    """
    from datetime import datetime

    total = 0
    current_year = datetime.utcnow().year
    for exp in cv.get("experiencia") or []:
        start = str(exp.get("fecha_inicio") or "")
        end = str(exp.get("fecha_fin") or "")
        actual = bool(exp.get("actual"))
        sy = _extract_year(start)
        if sy is None:
            continue
        if actual or not end:
            ey = current_year
        else:
            ey = _extract_year(end) or current_year
        years = max(0, min(ey - sy, 8))
        total += years
    return min(total, 40)


def _extract_year(s: str) -> int | None:
    m = re.search(r"(\d{4})", s or "")
    if not m:
        return None
    y = int(m.group(1))
    if 1970 <= y <= 2100:
        return y
    return None


def _offer_required_years(offer: str) -> int | None:
    """If the offer mentions N+ years of experience, return N. Else None."""
    m = re.search(r"(\d+)\s*\+?\s*(años|years|yrs)\s*(de\s+)?(experiencia|experience|exp)", offer or "", re.IGNORECASE)
    if m:
        return int(m.group(1))
    m = re.search(r"(experiencia|experience)\s+(mínimo|minima|min|of\s+at\s+least)?\s*(\d+)\s*\+?\s*(años|years|yrs)", offer or "", re.IGNORECASE)
    if m:
        return int(m.group(3))
    m = re.search(r"(\d+)\s*\+?\s*(años|years|yrs)", offer or "", re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None


# --- Main scoring -------------------------------------------------------


def score_match(cv: dict[str, Any], job_offer: str) -> dict[str, Any]:
    """Return a 0-100 score + breakdown for ``cv`` vs ``job_offer``.

    Returns a dict like::

        {
            "total": 72,
            "dimensions": {
                "tecnicas": {"weight": 60, "score": 45, "max": 60, "matched": [...], "missing": [...]},
                "idiomas":  {"weight": 20, "score": 15, "max": 20, "matched": [...], "missing": [...]},
                "experiencia": {"weight": 20, "score": 12, "max": 20, "cv_years": 5, "required_years": 3},
            },
            "summary": "7/9 skills · 2/2 idiomas · 5 años (≥3)",
        }
    """
    cv_techs = {_norm(s) for s in (cv.get("habilidades") or {}).get("tecnicas") or []}
    # Add experiencia / proyectos / tecnologias as a secondary source.
    for exp in cv.get("experiencia") or []:
        for b in (exp.get("responsabilidades") or []) + (exp.get("logros") or []):
            for k in _tokenize(b):
                if k in _KNOWN_TECH and k not in cv_techs:
                    cv_techs.add(k)
    for p in cv.get("proyectos") or []:
        for t in p.get("tecnologias") or []:
            n = _norm(str(t))
            if n and n not in cv_techs:
                cv_techs.add(n)
        for k in _tokenize(p.get("descripcion") or ""):
            if k in _KNOWN_TECH and k not in cv_techs:
                cv_techs.add(k)

    required_techs = _extract_tech_requirements(job_offer)
    if not required_techs:
        # If we can't extract anything, fall back to the union of CV techs
        # so the score doesn't penalise. Mark as "no signal".
        tech_score = 0
        tech_matched: list[str] = []
        tech_missing: list[str] = []
    else:
        tech_matched = sorted(t for t in required_techs if t in cv_techs)
        tech_missing = sorted(t for t in required_techs if t not in cv_techs)
        ratio = len(tech_matched) / len(required_techs)
        tech_score = round(60 * ratio)

    # --- idiomas ---
    required_langs = _extract_required_languages(job_offer)
    cv_langs = _cv_languages(cv)
    if not required_langs:
        lang_score = 0  # No signal: neutral.
        lang_matched: list[str] = []
        lang_missing: list[str] = []
    else:
        lang_matched = [lang for lang in required_langs if any(lang in c for c in cv_langs)]
        lang_missing = [lang for lang in required_langs if lang not in lang_matched]
        ratio = len(lang_matched) / len(required_langs)
        lang_score = round(20 * ratio)

    # --- experiencia ---
    years = _cv_years(cv)
    required_years = _offer_required_years(job_offer)
    if required_years is None:
        # Without a target, give partial credit just for having any experience.
        exp_score = 10 if years > 0 else 0
    else:
        if years >= required_years:
            exp_score = 20
        else:
            # Linear interpolation: 0 if years==0, full if years>=required.
            exp_score = round(20 * years / required_years)
            exp_score = max(0, min(20, exp_score))

    total = tech_score + lang_score + exp_score

    summary = _build_summary(
        tech_matched, tech_missing, required_techs,
        lang_matched, lang_missing, required_langs,
        years, required_years,
    )

    return {
        "total": total,
        "dimensions": {
            "tecnicas": {
                "weight": 60, "score": tech_score, "max": 60,
                "matched": tech_matched, "missing": tech_missing,
                "required": required_techs,
            },
            "idiomas": {
                "weight": 20, "score": lang_score, "max": 20,
                "matched": lang_matched, "missing": lang_missing,
                "required": required_langs,
            },
            "experiencia": {
                "weight": 20, "score": exp_score, "max": 20,
                "cv_years": years, "required_years": required_years,
            },
        },
        "summary": summary,
    }


def _build_summary(
    tech_matched, tech_missing, required_techs,
    lang_matched, lang_missing, required_langs,
    years, required_years,
) -> str:
    parts: list[str] = []
    if required_techs:
        parts.append(f"{len(tech_matched)}/{len(required_techs)} skills")
    if required_langs:
        parts.append(f"{len(lang_matched)}/{len(required_langs)} idiomas")
    if required_years is not None:
        parts.append(f"{years} años (≥{required_years})")
    elif years:
        parts.append(f"{years} años exp.")
    return " · ".join(parts) or "Sin oferta"


def badge_color(total: int) -> str:
    """Return a CSS class for the badge based on the score."""
    if total >= 75:
        return "badge-green"
    if total >= 50:
        return "badge-yellow"
    if total >= 25:
        return "badge-orange"
    return "badge-red"


__all__ = [
    "score_match",
    "extract_keywords",
    "badge_color",
]
