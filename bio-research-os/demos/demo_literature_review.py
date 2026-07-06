#!/usr/bin/env python3
"""
Demo 1: Literature Review Automation
====================================
Simulates an end-to-end literature review workflow:
  1. Search PubMed via NCBI E-utilities (with mock fallback)
  2. Extract & summarize abstracts
  3. Build a co-occurrence knowledge graph
  4. Identify knowledge gaps
  5. Generate a structured review outline

Outputs:
  - {output_dir}/lit_review_summary_table.csv
  - {output_dir}/lit_review_knowledge_gaps.txt
  - {output_dir}/lit_review_outline.md
  - {output_dir}/lit_review_knowledge_graph.png

Usage:
  python demo_literature_review.py --topic "microglia in Alzheimer's disease" --max_results 30 --output-dir outputs/literature
"""

import argparse
import csv
import os
import re
import sys
import textwrap
from collections import Counter, defaultdict
from typing import List, Dict, Any

import numpy as np
import pandas as pd

# Matplotlib configuration
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_outputs")
NCBI_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
NCBI_EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# A small stop-word list for entity extraction
STOP_WORDS = {
    "the", "and", "of", "to", "in", "a", "is", "that", "for", "it", "with",
    "as", "was", "on", "by", "from", "at", "an", "be", "this", "which",
    "or", "are", "we", "have", "has", "had", "not", "but", "they", "their",
    "been", "were", "of", "of", "cells", "cell", "expression", "analysis",
    "data", "study", "studies", "using", "used", "method", "results", "show",
    "shown", "effect", "effects", "level", "levels", "activity", "change",
    "changes", "increase", "decrease", "role", "roles", "function", "functions",
    "may", "also", "however", "thus", "therefore", "these", "those", "such",
    "can", "could", "would", "should", "will", "between", "among", "within",
    "after", "before", "during", "through", "over", "into", "up", "down",
    "more", "than", "only", "some", "all", "both", "each", "other", "another",
    "one", "two", "first", "second", "significant", "significantly", "recent",
    "new", "novel", "potential", "important", "key", "several", "various",
    "different", "similar", "compared", "including", "included", "found",
    "reported", "suggested", "proposed", "demonstrated", "indicated",
}

# Mock corpus for offline fallback
MOCK_CORPUS = [
    {
        "pmid": "12345678",
        "title": "Microglial activation in early Alzheimer's disease",
        "abstract": (
            "Microglia, the resident immune cells of the central nervous system, play a pivotal role "
            "in neuroinflammation during Alzheimer's disease. In this study, we examined microglial "
            "activation markers in post-mortem brain tissue from patients with early-stage Alzheimer's "
            "disease. We found increased expression of TNF-alpha and IL-6 in microglia surrounding "
            "amyloid plaques. These findings suggest that microglial-driven neuroinflammation contributes "
            "to disease progression. Therapeutic strategies targeting microglial activation may offer "
            "novel avenues for treatment."
        ),
        "year": 2021,
    },
    {
        "pmid": "23456789",
        "title": "TREM2 variants alter microglial response in Alzheimer's disease",
        "abstract": (
            "Triggering receptor expressed on myeloid cells 2 (TREM2) is a key regulator of microglial "
            "function. Rare variants in TREM2 are associated with increased risk of Alzheimer's disease. "
            "Here, we show that TREM2-deficient microglia exhibit impaired phagocytosis of amyloid-beta "
            "plaques. Single-cell RNA sequencing revealed distinct microglial states associated with TREM2 "
            "expression. Our results highlight the importance of TREM2-mediated microglial responses in "
            "maintaining brain homeostasis."
        ),
        "year": 2022,
    },
    {
        "pmid": "34567890",
        "title": "Single-cell transcriptomics of microglia in neurodegeneration",
        "abstract": (
            "Microglia display remarkable heterogeneity across different brain regions and disease states. "
            "Using single-cell RNA sequencing, we profiled microglial transcriptomes in Alzheimer's disease, "
            "Parkinson's disease, and healthy controls. We identified disease-specific microglial subpopulations, "
            "including a unique neurodegenerative-associated microglial state shared across AD and PD. "
            "This shared signature suggests convergent microglial mechanisms in neurodegenerative diseases."
        ),
        "year": 2023,
    },
    {
        "pmid": "45678901",
        "title": "Lipid metabolism in microglia during Alzheimer's disease progression",
        "abstract": (
            "Emerging evidence links microglial lipid metabolism to Alzheimer's disease pathogenesis. "
            "We investigated lipid droplet accumulation in microglia using imaging mass spectrometry. "
            "Microglia near amyloid plaques showed altered cholesterol ester and triglyceride profiles. "
            "Genetic ablation of cholesterol synthesis in microglia reduced neuroinflammation and improved "
            "cognitive deficits in mouse models. These findings implicate lipid dysregulation as a driver "
            "of microglial dysfunction in AD."
        ),
        "year": 2023,
    },
    {
        "pmid": "56789012",
        "title": "Microglia-synapse interactions in Alzheimer's disease",
        "abstract": (
            "Synapse loss is the strongest correlate of cognitive decline in Alzheimer's disease. "
            "Microglia regulate synaptic pruning during development, but their role in adult synaptic "
            "homeostasis remains unclear. We demonstrate that complement C3-dependent microglial phagocytosis "
            "mediates excessive synapse elimination in AD mouse models. Blocking C3a receptor signaling "
            "preserved synaptic density and rescued memory impairments. Understanding microglia-synapse "
            "crosstalk may reveal therapeutic targets for preventing synapse loss."
        ),
        "year": 2022,
    },
    {
        "pmid": "67890123",
        "title": "Cytokine networks in microglia and astrocyte communication in AD",
        "abstract": (
            "Neuroinflammation in Alzheimer's disease involves complex interactions between microglia and "
            "astrocytes. We mapped cytokine signaling networks between these glial cell types using "
            "multiplex protein profiling. IL-1 beta from activated microglia triggered A1 astrocyte "
            "reactive states, which subsequently released neurotoxic factors. Disrupting this "
            "microglia-astrocyte cytokine axis ameliorated neuronal damage in vitro. These findings "
            "highlight the importance of glial communication in AD neuroinflammation."
        ),
        "year": 2021,
    },
    {
        "pmid": "78901234",
        "title": "Microglial epigenetic changes in Alzheimer's disease models",
        "abstract": (
            "Epigenetic modifications regulate microglial gene expression during neuroinflammation. "
            "We profiled DNA methylation and histone modifications in microglia isolated from AD mouse "
            "models and human brain tissue. Differential methylation was observed at loci associated "
            "with immune response and phagocytosis genes. Histone deacetylase inhibitors restored "
            "microglial homeostatic gene expression patterns. These data suggest that epigenetic "
            "reprogramming contributes to sustained microglial activation in AD."
        ),
        "year": 2024,
    },
    {
        "pmid": "89012345",
        "title": "Sex differences in microglial response to amyloid pathology",
        "abstract": (
            "Sex differences influence Alzheimer's disease risk and progression. We compared microglial "
            "responses in male and female APP/PS1 mice. Female mice exhibited more robust microglial "
            "activation and higher expression of interferon response genes. Ovariectomy attenuated these "
            "sex differences, suggesting estrogen-mediated modulation of microglial function. Understanding "
            "sex-specific microglial biology may inform precision medicine approaches for AD."
        ),
        "year": 2023,
    },
    {
        "pmid": "90123456",
        "title": "Microglial clearance of tau aggregates in tauopathy models",
        "abstract": (
            "Tau pathology spreads through neural networks in Alzheimer's disease and related tauopathies. "
            "Microglia internalize and degrade extracellular tau, but this clearance mechanism becomes "
            "impaired with age. We show that boosting microglial autophagy enhances tau clearance and "
            "reduces seeding capacity. Transcription factor EB activation in microglia restored degradative "
            "function. These findings support microglial enhancement strategies for tauopathies."
        ),
        "year": 2024,
    },
    {
        "pmid": "01234567",
        "title": "Metabolic reprogramming of microglia in Alzheimer's disease",
        "abstract": (
            "Cellular metabolism shapes immune cell function. We investigated metabolic changes in "
            "microglia during Alzheimer's disease progression using metabolomics and Seahorse analysis. "
            "Disease-associated microglia displayed glycolytic shift and impaired oxidative phosphorylation. "
            "Modulating microglial metabolism through PFKFB3 inhibition restored homeostatic signatures. "
            "Metabolic interventions may represent a novel therapeutic strategy for AD."
        ),
        "year": 2024,
    },
]


def ensure_output_dir(output_dir: str = None) -> str:
    """Create output directory if it does not exist."""
    if output_dir is None:
        output_dir = OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def print_progress(msg: str) -> None:
    """Print a progress message to stderr."""
    print(f"[PROGRESS] {msg}", file=sys.stderr)


def fetch_pubmed_ids(topic: str, max_results: int, timeout: int = 30) -> List[str]:
    """
    Use NCBI E-utilities esearch to retrieve PubMed IDs for a query.
    Returns empty list on failure so caller can fall back to mock corpus.
    """
    try:
        import requests
        params = {
            "db": "pubmed",
            "term": topic,
            "retmax": max_results,
            "retmode": "json",
        }
        print_progress(f"Searching PubMed for: '{topic}' ...")
        resp = requests.get(NCBI_ESEARCH, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        idlist = data.get("esearchresult", {}).get("idlist", [])
        print_progress(f"Found {len(idlist)} PubMed IDs via API.")
        return idlist
    except Exception as exc:
        print_progress(f"PubMed esearch failed ({exc}); will use mock corpus.")
        return []


def fetch_pubmed_details(pmids: List[str], timeout: int = 30) -> List[Dict[str, Any]]:
    """
    Use NCBI E-utilities efetch to retrieve title/abstract for a list of PMIDs.
    Returns empty list on failure.
    """
    if not pmids:
        return []
    try:
        import requests
        ids = ",".join(pmids)
        params = {
            "db": "pubmed",
            "id": ids,
            "retmode": "xml",
        }
        print_progress("Fetching PubMed details via efetch ...")
        resp = requests.get(NCBI_EFETCH, params=params, timeout=timeout)
        resp.raise_for_status()
        # Very lightweight XML parsing of PubMedArticleSet
        text = resp.text
        articles = []
        # Split by PubmedArticle tags roughly
        raw_articles = text.split("<PubmedArticle>")
        for raw in raw_articles[1:]:
            pmid = ""
            title = ""
            abstract = ""
            year = ""
            pmid_m = re.search(r"<PMID[^>]*>(\d+)</PMID>", raw)
            if pmid_m:
                pmid = pmid_m.group(1)
            title_m = re.search(r"<ArticleTitle>(.*?)</ArticleTitle>", raw, re.DOTALL)
            if title_m:
                title = re.sub(r"\s+", " ", title_m.group(1).replace("\n", " "))
            # AbstractText may have multiple segments; concatenate
            abs_parts = re.findall(r"<AbstractText[^>]*>(.*?)</AbstractText>", raw, re.DOTALL)
            abstract = " ".join(re.sub(r"\s+", " ", p.replace("\n", " ")) for p in abs_parts)
            year_m = re.search(r"<PubDate>.*?<Year>(\d{4})</Year>.*?</PubDate>", raw, re.DOTALL)
            if year_m:
                year = int(year_m.group(1))
            if pmid and title:
                articles.append({
                    "pmid": pmid,
                    "title": title,
                    "abstract": abstract,
                    "year": year if year else None,
                })
        print_progress(f"Retrieved details for {len(articles)} articles.")
        return articles
    except Exception as exc:
        print_progress(f"PubMed efetch failed ({exc}); will use mock corpus.")
        return []


def extract_entities(text: str, min_len: int = 4) -> List[str]:
    """
    Naive entity extraction: split into words, lowercase, filter stop words and short tokens,
    keep only alphanumeric tokens that look like nouns (heuristic).
    """
    # Simple tokenization
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9_+-]+", text)
    entities = []
    for tok in tokens:
        t = tok.lower()
        if len(t) < min_len:
            continue
        if t in STOP_WORDS:
            continue
        # Keep words that look like nouns or known gene/protein names (heuristic: capitalized in original)
        # For this demo, keep all reasonable tokens
        entities.append(t)
    return entities


def build_cooccurrence_graph(articles: List[Dict[str, Any]], top_n: int = 40) -> "nx.Graph":
    """
    Build an entity co-occurrence graph from abstracts.
    Nodes = frequent entities; edges connect entities appearing in same abstract.
    """
    if not HAS_NETWORKX:
        print_progress("networkx not installed; skipping graph generation.")
        return None

    # Count entity frequencies across all abstracts
    entity_counts = Counter()
    abstract_entities = []
    for art in articles:
        entities = extract_entities(art.get("abstract", "") + " " + art.get("title", ""))
        abstract_entities.append(entities)
        entity_counts.update(entities)

    top_entities = {e for e, _ in entity_counts.most_common(top_n)}

    G = nx.Graph()
    cooccurrence = defaultdict(int)
    for entities in abstract_entities:
        filtered = [e for e in entities if e in top_entities]
        for i in range(len(filtered)):
            for j in range(i + 1, len(filtered)):
                a, b = sorted((filtered[i], filtered[j]))
                if a != b:
                    cooccurrence[(a, b)] += 1

    for (a, b), weight in cooccurrence.items():
        G.add_edge(a, b, weight=weight)

    # Add node frequencies as attributes
    for node in G.nodes():
        G.nodes[node]["freq"] = entity_counts[node]

    print_progress(f"Built co-occurrence graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    return G


def plot_knowledge_graph(G, topic: str, outpath: str) -> None:
    """Render the co-occurrence knowledge graph to a PNG file."""
    if G is None or not HAS_NETWORKX:
        print_progress("Graph not available for plotting.")
        return
    plt.figure(figsize=(12, 10))
    pos = nx.spring_layout(G, k=0.6, iterations=50, seed=42)
    freqs = np.array([G.nodes[n].get("freq", 1) for n in G.nodes()])
    node_sizes = 200 + (freqs - freqs.min()) / max(1, freqs.max() - freqs.min()) * 1800
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color="skyblue", alpha=0.9)
    nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.4, edge_color="gray")
    nx.draw_networkx_labels(G, pos, font_size=8, font_family="sans-serif")
    plt.title(f"Entity Co-occurrence Graph: {topic}", fontsize=14)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()
    print_progress(f"Saved knowledge graph to {outpath}")


def summarize_abstract(abstract: str, sentence_count: int = 2) -> str:
    """
    Very simple extractive summarization: score sentences by entity density,
    pick top sentences.
    """
    sentences = re.split(r"(?<=[.!?])\s+", abstract)
    if len(sentences) <= sentence_count:
        return abstract
    scores = []
    for s in sentences:
        ents = extract_entities(s)
        scores.append(len(ents) / max(1, len(s.split())))
    ranked = np.argsort(scores)[::-1]
    chosen = sorted(ranked[:sentence_count])
    return " ".join(sentences[i] for i in chosen)


def identify_knowledge_gaps(articles: List[Dict[str, Any]], topic: str) -> List[str]:
    """
    Heuristic gap detection based on entity frequency and co-occurrence.
    Identifies under-studied connections and missing study types.
    """
    gaps = []
    all_entities = Counter()
    year_counts = Counter()
    study_types = Counter()
    for art in articles:
        text = (art.get("title", "") + " " + art.get("abstract", "")).lower()
        year_counts[art.get("year", "unknown")] += 1
        # Detect study type heuristics
        if "single-cell" in text or "single cell" in text or "scrna-seq" in text:
            study_types["single-cell transcriptomics"] += 1
        if "mouse model" in text or "app/ps1" in text or "transgenic" in text:
            study_types["animal model"] += 1
        if "human" in text or "patient" in text or "post-mortem" in text:
            study_types["human clinical/post-mortem"] += 1
        if "epigenetic" in text or "methylation" in text or "histone" in text:
            study_types["epigenetics"] += 1
        if "metabol" in text:
            study_types["metabolomics"] += 1
        all_entities.update(extract_entities(text))

    # Gap 1: If few recent papers
    recent_years = [y for y in year_counts if isinstance(y, int) and y >= 2023]
    if len(recent_years) < 2:
        gaps.append("Limited very recent (2023+) studies; emerging mechanisms may be underexplored.")

    # Gap 2: Missing study types
    if study_types["single-cell transcriptomics"] < 2:
        gaps.append("Sparse single-cell resolution data; cellular heterogeneity may be overlooked.")
    if study_types["metabolomics"] < 2:
        gaps.append("Metabolic profiling of microglia remains underrepresented despite emerging relevance.")
    if study_types["epigenetics"] < 2:
        gaps.append("Epigenetic regulation in microglia during disease progression is understudied.")

    # Gap 3: Sex differences
    sex_mentions = sum(1 for art in articles if "sex" in (art.get("title", "") + art.get("abstract", "")).lower())
    if sex_mentions < 2:
        gaps.append("Sex-specific microglial responses are rarely addressed; precision medicine potential untapped.")

    # Gap 4: Therapeutic translation
    therapy_mentions = sum(1 for art in articles if "therapeutic" in (art.get("title", "") + art.get("abstract", "")).lower()
                            or "treatment" in (art.get("title", "") + art.get("abstract", "")).lower())
    if therapy_mentions < 3:
        gaps.append("Translational and therapeutic-oriented studies are limited; mechanistic findings lack clinical validation.")

    # Generic fallback if gaps are few
    if len(gaps) < 3:
        gaps.append("Longitudinal studies tracking microglial changes across disease stages are scarce.")
        gaps.append("Integration of multi-omics data (genomics, transcriptomics, proteomics) in microglial research is limited.")

    return gaps[:5]


def generate_review_outline(topic: str, articles: List[Dict[str, Any]], gaps: List[str]) -> str:
    """Generate a structured markdown review outline."""
    sections = [
        f"# Systematic Review Outline: {topic}",
        "",
        "## 1. Introduction",
        f"- **Background**: Overview of {topic} and its significance.",
        "- **Objectives**: Summarize current evidence, identify gaps, and propose future directions.",
        "",
        "## 2. Methods",
        f"- **Search Strategy**: PubMed search for '{topic}'.",
        f"- **Inclusion Criteria**: English-language articles with available abstracts (n={len(articles)}).",
        "- **Data Extraction**: Titles, abstracts, publication years, and key entities.",
        "",
        "## 3. Results",
        "### 3.1 Publication Trends",
        "- Temporal distribution of included studies.",
        "### 3.2 Key Themes",
        "- Microglial activation and neuroinflammation.",
        "- Genetic risk factors (e.g., TREM2 variants).",
        "- Lipid metabolism and metabolic reprogramming.",
        "- Microglia-synapse interactions and synaptic pruning.",
        "- Sex differences in microglial biology.",
        "### 3.3 Knowledge Graph Summary",
        "- Co-occurrence network of top entities extracted from abstracts.",
        "",
        "## 4. Discussion",
        "### 4.1 Major Findings",
        "- Synthesis of mechanistic insights from included studies.",
        "### 4.2 Knowledge Gaps",
    ]
    for g in gaps:
        sections.append(f"- {g}")
    sections += [
        "",
        "## 5. Future Directions",
        "- Prioritize single-cell and spatial transcriptomics to resolve microglial heterogeneity.",
        "- Integrate multi-omics datasets for systems-level understanding.",
        "- Develop microglia-targeted therapeutics with biomarker-guided patient stratification.",
        "",
        "## 6. Conclusion",
        f"- {topic} represents a dynamic and rapidly evolving field with significant translational potential.",
    ]
    return "\n".join(sections)


def save_summary_table(articles: List[Dict[str, Any]], outpath: str) -> None:
    """Save a CSV summary of articles with one-sentence summaries."""
    rows = []
    for art in articles:
        rows.append({
            "PMID": art.get("pmid", ""),
            "Year": art.get("year", ""),
            "Title": art.get("title", ""),
            "Abstract_Summary": summarize_abstract(art.get("abstract", ""), sentence_count=2),
        })
    df = pd.DataFrame(rows)
    df.to_csv(outpath, index=False, encoding="utf-8-sig")
    print_progress(f"Saved summary table to {outpath}")


def save_knowledge_gaps(gaps: List[str], outpath: str) -> None:
    """Save knowledge gap list to a text file."""
    with open(outpath, "w", encoding="utf-8") as fh:
        fh.write("Knowledge Gaps Identified\n")
        fh.write("=" * 50 + "\n\n")
        for idx, g in enumerate(gaps, 1):
            fh.write(f"{idx}. {g}\n")
    print_progress(f"Saved knowledge gaps to {outpath}")


def main():
    parser = argparse.ArgumentParser(
        description="Literature Review Automation Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(__doc__),
    )
    parser.add_argument(
        "--topic",
        type=str,
        default="microglia in Alzheimer's disease",
        help="Research topic to search and review (default: 'microglia in Alzheimer's disease').",
    )
    parser.add_argument(
        "--max_results",
        type=int,
        default=30,
        help="Maximum number of PubMed results to retrieve (default: 30).",
    )
    parser.add_argument(
        "--use_mock",
        action="store_true",
        help="Force usage of the built-in mock corpus instead of PubMed API.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (default: demo_outputs/).",
    )
    args = parser.parse_args()

    out_dir = ensure_output_dir(args.output_dir)

    # Step 1: Retrieve articles
    if args.use_mock:
        print_progress("Using mock corpus as requested.")
        articles = MOCK_CORPUS[: args.max_results]
    else:
        pmids = fetch_pubmed_ids(args.topic, args.max_results)
        if pmids:
            articles = fetch_pubmed_details(pmids)
        else:
            print_progress("Falling back to mock corpus.")
            articles = MOCK_CORPUS[: args.max_results]

    if not articles:
        print_progress("No articles retrieved. Exiting.")
        sys.exit(1)

    print_progress(f"Proceeding with {len(articles)} articles.")

    # Step 2: Summarize and save table
    summary_path = os.path.join(out_dir, "lit_review_summary_table.csv")
    save_summary_table(articles, summary_path)

    # Step 3: Build knowledge graph
    G = build_cooccurrence_graph(articles, top_n=40)
    graph_path = os.path.join(out_dir, "lit_review_knowledge_graph.png")
    plot_knowledge_graph(G, args.topic, graph_path)

    # Step 4: Identify knowledge gaps
    gaps = identify_knowledge_gaps(articles, args.topic)
    gaps_path = os.path.join(out_dir, "lit_review_knowledge_gaps.txt")
    save_knowledge_gaps(gaps, gaps_path)

    # Step 5: Generate review outline
    outline = generate_review_outline(args.topic, articles, gaps)
    outline_path = os.path.join(out_dir, "lit_review_outline.md")
    with open(outline_path, "w", encoding="utf-8") as fh:
        fh.write(outline)
    print_progress(f"Saved review outline to {outline_path}")

    # Final summary to stdout
    print("\n" + "=" * 60)
    print("Literature Review Automation Complete")
    print("=" * 60)
    print(f"Output directory       : {out_dir}")
    print(f"Articles processed     : {len(articles)}")
    print(f"Summary table          : {summary_path}")
    print(f"Knowledge graph        : {graph_path}")
    print(f"Knowledge gaps         : {gaps_path}")
    print(f"Review outline         : {outline_path}")
    print("\nTop entities (from abstracts):")
    if G is not None and HAS_NETWORKX:
        top_nodes = sorted(G.nodes(data=True), key=lambda x: x[1].get("freq", 0), reverse=True)[:10]
        for node, data in top_nodes:
            print(f"  - {node}: {data.get('freq', 0)} mentions")
    else:
        print("  (Graph not available)")
    print("\nIdentified Knowledge Gaps:")
    for idx, g in enumerate(gaps, 1):
        print(f"  {idx}. {g}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
