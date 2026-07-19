"""
Extrae highlights y comentarios del tutor de un PDF y los exporta a JSON.
Uso: python extract_pdf_annotations.py <ruta_pdf> [ruta_salida.json]
"""

import sys
import json
import fitz  # PyMuPDF

# Tipos de anotación que nos interesan
ANNOT_TYPES = {
    fitz.PDF_ANNOT_HIGHLIGHT:      "Highlight",
    fitz.PDF_ANNOT_UNDERLINE:      "Underline",
    fitz.PDF_ANNOT_SQUIGGLY:       "Squiggly",
    fitz.PDF_ANNOT_STRIKE_OUT:     "StrikeOut",
    fitz.PDF_ANNOT_FREE_TEXT:      "FreeText",
    fitz.PDF_ANNOT_TEXT:           "Note",
}


def extract_highlighted_text(page, annot):
    """Extrae el texto bajo los rectángulos de la anotación."""
    quads = annot.vertices
    if not quads:
        return ""

    texts = []
    # Los vértices vienen en grupos de 4 puntos (quad)
    for i in range(0, len(quads), 4):
        quad = fitz.Quad(quads[i:i+4])
        words = page.get_text("words", clip=quad.rect)
        texts.append(" ".join(w[4] for w in words))

    return " ".join(texts).strip()


def extract_annotations(pdf_path):
    doc = fitz.open(pdf_path)
    results = []

    for page_num, page in enumerate(doc, start=1):
        for annot in page.annots():
            annot_type = annot.type[0]
            if annot_type not in ANNOT_TYPES:
                continue

            tipo = ANNOT_TYPES[annot_type]
            comentario = (annot.info.get("content") or "").strip()
            autor = (annot.info.get("title") or "").strip()

            # Texto resaltado (solo tiene sentido en marcas de texto)
            if annot_type in (
                fitz.PDF_ANNOT_HIGHLIGHT,
                fitz.PDF_ANNOT_UNDERLINE,
                fitz.PDF_ANNOT_SQUIGGLY,
                fitz.PDF_ANNOT_STRIKE_OUT,
            ):
                texto_resaltado = extract_highlighted_text(page, annot)
            elif annot_type == fitz.PDF_ANNOT_FREE_TEXT:
                # El texto está dentro de la anotación misma
                texto_resaltado = comentario
                comentario = ""
            else:
                texto_resaltado = ""

            # Si no hay ni texto ni comentario, saltar
            if not texto_resaltado and not comentario:
                continue

            entry = {
                "pagina": page_num,
                "tipo": tipo,
                "texto_resaltado": texto_resaltado,
                "comentario_tutor": comentario,
            }
            if autor:
                entry["autor"] = autor

            results.append(entry)

    doc.close()
    return results


def main():
    if len(sys.argv) < 2:
        print("Uso: python extract_pdf_annotations.py <ruta_pdf> [salida.json]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else pdf_path.replace(".pdf", "_anotaciones.json")

    print(f"Procesando: {pdf_path}")
    annotations = extract_annotations(pdf_path)

    if not annotations:
        print("No se encontraron anotaciones en el PDF.")
        sys.exit(0)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(annotations, f, ensure_ascii=False, indent=2)

    print(f"Extraidas {len(annotations)} anotaciones -> {output_path}")

    # Preview en consola
    print("\n--- PREVIEW (primeras 5) ---")
    for a in annotations[:5]:
        print(f"\n[Pág. {a['pagina']}] {a['tipo']}")
        if a["texto_resaltado"]:
            print(f"  Texto:      {a['texto_resaltado'][:120]}")
        if a["comentario_tutor"]:
            print(f"  Comentario: {a['comentario_tutor'][:200]}")


if __name__ == "__main__":
    main()
