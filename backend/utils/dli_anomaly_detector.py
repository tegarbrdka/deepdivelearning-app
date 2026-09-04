"""
DLI Anomaly Detector
====================
Mendeteksi anomali pada hasil analisis DLI untuk keperluan validasi sistem.

Anomali yang dideteksi:
1. Grade 4 (DLI >= 70%) tapi skor aspek tertentu < 70%
2. Grade 1 (DLI < 40%) tapi ada aspek yang > 60%
3. Grade 2/3 (40-70%) tapi ada aspek yang > 80%
4. Keyword indikator yang paling jarang muncul pada dokumen Grade 4
5. Kata pedagogis yang sering muncul di Grade 4 tapi belum ada di kamus (keyword gap)

Penggunaan:
    python backend/utils/dli_anomaly_detector.py --db ./educlassify.db
    python backend/utils/dli_anomaly_detector.py --db ./educlassify.db --export anomali.csv
"""

import json
import re
import sqlite3
import argparse
from collections import defaultdict
from pathlib import Path
from pathlib import Path


# Grade boundaries
GRADE_4_MIN = 70.0   # Siap Implementasi
GRADE_3_MIN = 55.0
GRADE_2_MIN = 40.0
# Grade 1 = < 40%

ASPECTS = ['mindful', 'meaningful', 'joyful', 'pedagogis', 'digital']


def get_grade(dli_score: float) -> int:
    if dli_score >= GRADE_4_MIN:
        return 4
    elif dli_score >= GRADE_3_MIN:
        return 3
    elif dli_score >= GRADE_2_MIN:
        return 2
    return 1


def load_all_keywords() -> set:
    """Load semua keyword yang sudah ada di kamus sebagai set lowercase."""
    keywords_dir = Path(__file__).parent.parent / 'ai' / 'dli' / 'keywords'
    all_kw = set()
    for f in keywords_dir.glob('*.json'):
        data = json.load(open(f, encoding='utf-8'))
        for sub in data.values():
            for strength_list in sub.values():
                for kw in strength_list:
                    all_kw.add(kw.lower())
    return all_kw


# Kata-kata pedagogis yang relevan untuk dicari (bigram/trigram)
PEDAGOGIS_PATTERNS = re.compile(
    r'\b(siswa\s+\w+|murid\s+\w+|peserta\s+didik\s+\w+|'
    r'guru\s+\w+|pembelajaran\s+\w+|aktivitas\s+\w+|'
    r'diskusi\s+\w+|refleksi\s+\w+|kolaborasi\s+\w+|'
    r'proyek\s+\w+|presentasi\s+\w+|eksplorasi\s+\w+|'
    r'analisis\s+\w+|evaluasi\s+\w+|kreasi\s+\w+)\b',
    re.IGNORECASE
)


def load_dli_predictions(db_path: str) -> list[dict]:
    """Ambil semua prediksi yang memiliki data DLI dari database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, file_name, dli_score, dli_category,
               mindful_score, meaningful_score, joyful_score,
               pedagogis_score, digital_score, dli_data, created_at
        FROM predictions
        WHERE dli_score IS NOT NULL
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        record = dict(row)
        if record['dli_data']:
            try:
                full = json.loads(record['dli_data']) if isinstance(record['dli_data'], str) else record['dli_data']
                record['keywords_found'] = full.get('keywords_found', {})
                record['keyword_statistics'] = full.get('keyword_statistics', {})
                record['_full_data'] = full
            except Exception:
                record['keywords_found'] = {}
                record['keyword_statistics'] = {}
                record['_full_data'] = {}
        else:
            record['keywords_found'] = {}
            record['keyword_statistics'] = {}
            record['_full_data'] = {}
        results.append(record)

    return results


def detect_anomalies(predictions: list[dict]) -> dict:
    """Jalankan semua pemeriksaan anomali."""

    anomaly_1 = []  # Grade 4 tapi ada aspek < 70%
    anomaly_2 = []  # Grade 1 tapi ada aspek > 60%
    anomaly_3 = []  # Grade 2/3 tapi ada aspek > 80%
    keyword_freq_grade4 = defaultdict(int)  # frekuensi keyword di Grade 4

    for pred in predictions:
        dli = pred['dli_score']
        grade = get_grade(dli)
        fname = pred.get('file_name', f"ID:{pred['id']}")

        scores = {
            'mindful':    pred.get('mindful_score', 0) or 0,
            'meaningful': pred.get('meaningful_score', 0) or 0,
            'joyful':     pred.get('joyful_score', 0) or 0,
            'pedagogis':  pred.get('pedagogis_score', 0) or 0,
            'digital':    pred.get('digital_score', 0) or 0,
        }

        # --- Anomali 1: Grade 4 tapi ada aspek < 70% ---
        if grade == 4:
            weak_aspects = {k: v for k, v in scores.items() if v < 70.0}
            if weak_aspects:
                anomaly_1.append({
                    'file': fname,
                    'dli_score': dli,
                    'grade': 4,
                    'weak_aspects': weak_aspects,
                    'all_scores': scores,
                    'anomaly': 'Grade 4 tapi aspek lemah < 70%'
                })

            # Kumpulkan keyword untuk analisis frekuensi
            kw = pred.get('keywords_found', {})
            for color, words in kw.items():
                if color == 'green':  # hanya keyword positif
                    for w in words:
                        keyword_freq_grade4[w] += 1

        # --- Anomali 2: Grade 1 tapi ada aspek > 60% ---
        elif grade == 1:
            strong_aspects = {k: v for k, v in scores.items() if v > 60.0}
            if strong_aspects:
                anomaly_2.append({
                    'file': fname,
                    'dli_score': dli,
                    'grade': 1,
                    'strong_aspects': strong_aspects,
                    'all_scores': scores,
                    'anomaly': 'Grade 1 tapi ada aspek kuat > 60%'
                })

        # --- Anomali 3: Grade 2/3 tapi ada aspek > 80% ---
        elif grade in (2, 3):
            very_strong = {k: v for k, v in scores.items() if v > 80.0}
            if very_strong:
                anomaly_3.append({
                    'file': fname,
                    'dli_score': dli,
                    'grade': grade,
                    'very_strong_aspects': very_strong,
                    'all_scores': scores,
                    'anomaly': f'Grade {grade} tapi ada aspek sangat kuat > 80%'
                })

    # --- Anomali 4: Keyword paling jarang di Grade 4 ---
    rare_keywords = []
    total_grade4 = sum(1 for p in predictions if get_grade(p['dli_score']) == 4)
    if keyword_freq_grade4:
        sorted_kw = sorted(keyword_freq_grade4.items(), key=lambda x: x[1])
        rare_keywords = [
            {
                'keyword': kw,
                'frekuensi': freq,
                'persen_dokumen_grade4': round(freq / max(total_grade4, 1) * 100, 1)
            }
            for kw, freq in sorted_kw[:10]
        ]

    # --- Anomali 5: Keyword gap — frasa pedagogis di Grade 4 yang belum ada di kamus ---
    keyword_gap = _find_keyword_gaps(predictions)

    return {
        'anomali_1_grade4_aspek_lemah': anomaly_1,
        'anomali_2_grade1_aspek_kuat': anomaly_2,
        'anomali_3_grade23_aspek_sangat_kuat': anomaly_3,
        'anomali_4_keyword_jarang_grade4': rare_keywords,
        'anomali_5_keyword_gap': keyword_gap,
        'ringkasan': {
            'total_prediksi_dli': len(predictions),
            'grade_4': total_grade4,
            'grade_3': sum(1 for p in predictions if get_grade(p['dli_score']) == 3),
            'grade_2': sum(1 for p in predictions if get_grade(p['dli_score']) == 2),
            'grade_1': sum(1 for p in predictions if get_grade(p['dli_score']) == 1),
            'total_anomali_1': len(anomaly_1),
            'total_anomali_2': len(anomaly_2),
            'total_anomali_3': len(anomaly_3),
            'total_keyword_gap': len(keyword_gap),
        }
    }


def _find_keyword_gaps(predictions: list[dict]) -> list[dict]:
    """
    Cari frasa pedagogis yang sering muncul di dokumen Grade 4
    tapi belum ada di kamus keyword.
    Menggunakan teks yang tersimpan di dli_data.
    """
    existing_kw = load_all_keywords()
    candidate_freq = defaultdict(int)
    grade4_docs = [p for p in predictions if get_grade(p['dli_score']) == 4]

    for pred in grade4_docs:
        # Ambil teks dari highlighted_text (strip HTML tags)
        full_data = pred.get('_full_data', {})
        highlighted = full_data.get('highlighted_text', '')
        if not highlighted:
            continue

        # Strip HTML tags
        clean_text = re.sub(r'<[^>]+>', ' ', highlighted).lower()

        # Cari frasa pedagogis (bigram dengan kata kerja aktif)
        matches = PEDAGOGIS_PATTERNS.findall(clean_text)
        for match in matches:
            phrase = ' '.join(match.lower().split())
            if phrase not in existing_kw and len(phrase) > 5:
                candidate_freq[phrase] += 1

    # Kembalikan 20 kandidat terbanyak
    sorted_candidates = sorted(candidate_freq.items(), key=lambda x: -x[1])
    return [
        {'frasa': phrase, 'frekuensi': freq, 'saran': 'Pertimbangkan menambahkan ke kamus keyword'}
        for phrase, freq in sorted_candidates[:20]
        if freq >= 2  # minimal muncul di 2 dokumen
    ]


def print_report(result: dict):
    """Cetak laporan anomali ke terminal."""
    r = result['ringkasan']
    print("\n" + "=" * 70)
    print("  LAPORAN ANOMALI DLI")
    print("=" * 70)
    print(f"\nTotal prediksi DLI: {r['total_prediksi_dli']}")
    print(f"  Grade 4 (>=70%): {r['grade_4']} dokumen")
    print(f"  Grade 3 (55-70%): {r['grade_3']} dokumen")
    print(f"  Grade 2 (40-55%): {r['grade_2']} dokumen")
    print(f"  Grade 1 (<40%): {r['grade_1']} dokumen")

    # Anomali 1
    print(f"\n{'-'*70}")
    print(f"ANOMALI 1: Grade 4 tapi ada aspek < 70%  [{r['total_anomali_1']} kasus]")
    print("  -> Indikasi: bobot aspek tidak seimbang atau keyword aspek tertentu kurang")
    for a in result['anomali_1_grade4_aspek_lemah']:
        print(f"\n  [DOC] {a['file']}")
        print(f"     DLI: {a['dli_score']:.1f}%  (Grade 4)")
        for asp, sc in a['weak_aspects'].items():
            print(f"     [!] {asp}: {sc:.1f}%")

    # Anomali 2
    print(f"\n{'-'*70}")
    print(f"ANOMALI 2: Grade 1 tapi ada aspek > 60%  [{r['total_anomali_2']} kasus]")
    print("  -> Indikasi: aspek lain sangat lemah sehingga menarik rata-rata ke bawah")
    for a in result['anomali_2_grade1_aspek_kuat']:
        print(f"\n  [DOC] {a['file']}")
        print(f"     DLI: {a['dli_score']:.1f}%  (Grade 1)")
        for asp, sc in a['strong_aspects'].items():
            print(f"     [OK] {asp}: {sc:.1f}%")

    # Anomali 3
    print(f"\n{'-'*70}")
    print(f"ANOMALI 3: Grade 2/3 tapi ada aspek > 80%  [{r['total_anomali_3']} kasus]")
    print("  -> Indikasi: RPP sangat kuat di satu aspek tapi sangat lemah di aspek lain")
    for a in result['anomali_3_grade23_aspek_sangat_kuat']:
        print(f"\n  [DOC] {a['file']}")
        print(f"     DLI: {a['dli_score']:.1f}%  (Grade {a['grade']})")
        for asp, sc in a['very_strong_aspects'].items():
            print(f"     [**] {asp}: {sc:.1f}%")

    # Anomali 4
    print(f"\n{'-'*70}")
    print("ANOMALI 4: Keyword paling jarang muncul di dokumen Grade 4")
    print("  -> Indikasi: keyword ini mungkin terlalu spesifik atau perlu sinonim")
    if result['anomali_4_keyword_jarang_grade4']:
        for kw in result['anomali_4_keyword_jarang_grade4']:
            print(f"  [KW] \"{kw['keyword']}\"  -- muncul {kw['frekuensi']}x "
                  f"({kw['persen_dokumen_grade4']}% dokumen Grade 4)")
    else:
        print("  (Belum ada data Grade 4 yang cukup)")

    # Anomali 5
    print(f"\n{'-'*70}")
    print("ANOMALI 5: Frasa pedagogis yang belum ada di kamus keyword (Keyword Gap)")
    print("  -> Indikasi: kata-kata ini sering digunakan guru tapi belum terdeteksi sistem")
    if result.get('anomali_5_keyword_gap'):
        for item in result['anomali_5_keyword_gap']:
            print(f"  [GAP] \"{item['frasa']}\"  -- muncul {item['frekuensi']}x di dokumen Grade 4")
    else:
        print("  (Tidak ada gap yang terdeteksi atau belum ada data teks yang cukup)")

    print("\n" + "=" * 70)


def export_csv(result: dict, output_path: str):
    """Export hasil anomali ke CSV."""
    import csv

    rows = []
    for a in result['anomali_1_grade4_aspek_lemah']:
        rows.append({'tipe': 'Anomali 1', 'file': a['file'],
                     'dli_score': a['dli_score'], 'grade': 4,
                     'detail': str(a['weak_aspects'])})
    for a in result['anomali_2_grade1_aspek_kuat']:
        rows.append({'tipe': 'Anomali 2', 'file': a['file'],
                     'dli_score': a['dli_score'], 'grade': 1,
                     'detail': str(a['strong_aspects'])})
    for a in result['anomali_3_grade23_aspek_sangat_kuat']:
        rows.append({'tipe': 'Anomali 3', 'file': a['file'],
                     'dli_score': a['dli_score'], 'grade': a['grade'],
                     'detail': str(a['very_strong_aspects'])})

    if not rows:
        print("Tidak ada anomali untuk diekspor.")
        return

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['tipe', 'file', 'dli_score', 'grade', 'detail'])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✅ Hasil anomali diekspor ke: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='DLI Anomaly Detector')
    parser.add_argument('--db', default='./educlassify.db', help='Path ke database SQLite')
    parser.add_argument('--export', default=None, help='Export hasil ke file CSV')
    parser.add_argument('--json', action='store_true', help='Output dalam format JSON')
    args = parser.parse_args()

    if not Path(args.db).exists():
        print(f"❌ Database tidak ditemukan: {args.db}")
        return

    print(f"[DB] Membaca database: {args.db}")
    predictions = load_dli_predictions(args.db)

    if not predictions:
        print("⚠️  Belum ada data DLI di database. Lakukan analisis DLI terlebih dahulu.")
        return

    result = detect_anomalies(predictions)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_report(result)

    if args.export:
        export_csv(result, args.export)


if __name__ == '__main__':
    main()
