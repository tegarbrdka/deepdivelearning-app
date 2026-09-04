import re

path = r'f:\educlasify\frontend\src\pages\user\VideoAnalysis3MResult.jsx'

with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

if "useLang" not in c:
    c = c.replace("import { motion } from 'framer-motion';", "import { motion } from 'framer-motion';\nimport { useLang } from '../../contexts/LanguageContext';")
    c = c.replace("const VideoAnalysis3MResult = () => {", "const VideoAnalysis3MResult = () => {\n  const { t } = useLang();")

c = c.replace('title="Detail Sub-Skor per Dimensi"', "title={t('video3m.panelScores')}")
c = c.replace('title="Rekomendasi"', "title={t('video3m.panelRecommendations')}")
c = c.replace('>Hasil Analisis 3M<', ">{t('video3m.resultTitle')}<")
c = c.replace('>Export CSV<', ">{t('video3m.exportCsv')}<")
c = c.replace('>Export PDF<', ">{t('video3m.exportPdf')}<")
c = c.replace('title="Skor 3M"', "title={t('video3m.panelScores')}")
c = c.replace('title="Distribusi Waktu Bicara"', "title={t('video3m.panelTalkTime')}")
c = c.replace('title="Timeline Pedagogis per Fragmen"', "title={t('video3m.panelTimeline')}")
c = c.replace('title="Peta Kolaborasi Kelas"', "title={t('video3m.panelHeatmap')}")
c = c.replace('title="Klip Bukti"', "title={t('video3m.panelEvidence')}")
c = c.replace('title="Triangulasi RPP"', "title={t('video3m.panelTriangulation')}")
c = c.replace('>Analisis Video 3M<', ">{t('video3m.uploadTitle')}<")

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)

print("Done")
