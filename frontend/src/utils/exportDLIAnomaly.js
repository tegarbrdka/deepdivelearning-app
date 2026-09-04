import jsPDF from 'jspdf'
import 'jspdf-autotable'
import { Document, Packer, Paragraph, TextRun, Table, TableCell, TableRow, HeadingLevel, AlignmentType, WidthType } from 'docx'
import { saveAs } from 'file-saver'

// Helper to format date
const formatDate = () => {
  const now = new Date()
  return now.toLocaleDateString('id-ID', { 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Export to PDF
export const exportToPDF = (data, t) => {
  const doc = new jsPDF()
  const pageWidth = doc.internal.pageSize.getWidth()
  let yPos = 20

  // Title
  doc.setFontSize(18)
  doc.setFont(undefined, 'bold')
  doc.text('Laporan Anomali DLI', pageWidth / 2, yPos, { align: 'center' })
  
  yPos += 10
  doc.setFontSize(10)
  doc.setFont(undefined, 'normal')
  doc.text(`Tanggal: ${formatDate()}`, pageWidth / 2, yPos, { align: 'center' })
  
  yPos += 15

  // Summary Statistics
  const r = data.ringkasan
  doc.setFontSize(12)
  doc.setFont(undefined, 'bold')
  doc.text('Ringkasan', 14, yPos)
  yPos += 8

  const summaryData = [
    ['Total Prediksi DLI', r.total_prediksi_dli],
    ['Grade 4', r.grade_4],
    ['Grade 3', r.grade_3],
    ['Grade 2', r.grade_2],
    ['Grade 1', r.grade_1],
    ['Total Anomali 1', r.total_anomali_1],
    ['Total Anomali 2', r.total_anomali_2],
    ['Total Anomali 3', r.total_anomali_3],
  ]

  doc.autoTable({
    startY: yPos,
    head: [['Metrik', 'Nilai']],
    body: summaryData,
    theme: 'grid',
    headStyles: { fillColor: [99, 102, 241] },
    margin: { left: 14, right: 14 },
  })

  yPos = doc.lastAutoTable.finalY + 15

  // Anomaly 1
  if (data.anomali_1_grade4_aspek_lemah.length > 0) {
    doc.addPage()
    yPos = 20
    doc.setFontSize(12)
    doc.setFont(undefined, 'bold')
    doc.text('Anomali 1: Grade 4 dengan Aspek Lemah', 14, yPos)
    yPos += 8

    const anomaly1Data = data.anomali_1_grade4_aspek_lemah.map(item => [
      item.file,
      `${item.dli_score?.toFixed(1)}%`,
      Object.entries(item.weak_aspects).map(([k, v]) => `${k}: ${v?.toFixed(1)}%`).join(', ')
    ])

    doc.autoTable({
      startY: yPos,
      head: [['File', 'DLI Score', 'Aspek Lemah']],
      body: anomaly1Data,
      theme: 'grid',
      headStyles: { fillColor: [249, 115, 22] },
      margin: { left: 14, right: 14 },
      columnStyles: {
        0: { cellWidth: 60 },
        1: { cellWidth: 30 },
        2: { cellWidth: 'auto' }
      }
    })
  }

  // Anomaly 2
  if (data.anomali_2_grade1_aspek_kuat.length > 0) {
    doc.addPage()
    yPos = 20
    doc.setFontSize(12)
    doc.setFont(undefined, 'bold')
    doc.text('Anomali 2: Grade 1 dengan Aspek Kuat', 14, yPos)
    yPos += 8

    const anomaly2Data = data.anomali_2_grade1_aspek_kuat.map(item => [
      item.file,
      `${item.dli_score?.toFixed(1)}%`,
      Object.entries(item.strong_aspects).map(([k, v]) => `${k}: ${v?.toFixed(1)}%`).join(', ')
    ])

    doc.autoTable({
      startY: yPos,
      head: [['File', 'DLI Score', 'Aspek Kuat']],
      body: anomaly2Data,
      theme: 'grid',
      headStyles: { fillColor: [239, 68, 68] },
      margin: { left: 14, right: 14 },
      columnStyles: {
        0: { cellWidth: 60 },
        1: { cellWidth: 30 },
        2: { cellWidth: 'auto' }
      }
    })
  }

  // Anomaly 3
  if (data.anomali_3_grade23_aspek_sangat_kuat.length > 0) {
    doc.addPage()
    yPos = 20
    doc.setFontSize(12)
    doc.setFont(undefined, 'bold')
    doc.text('Anomali 3: Grade 2/3 dengan Aspek Sangat Kuat', 14, yPos)
    yPos += 8

    const anomaly3Data = data.anomali_3_grade23_aspek_sangat_kuat.map(item => [
      item.file,
      `Grade ${item.grade}`,
      `${item.dli_score?.toFixed(1)}%`,
      Object.entries(item.very_strong_aspects).map(([k, v]) => `${k}: ${v?.toFixed(1)}%`).join(', ')
    ])

    doc.autoTable({
      startY: yPos,
      head: [['File', 'Grade', 'DLI Score', 'Aspek Sangat Kuat']],
      body: anomaly3Data,
      theme: 'grid',
      headStyles: { fillColor: [251, 191, 36] },
      margin: { left: 14, right: 14 },
      columnStyles: {
        0: { cellWidth: 50 },
        1: { cellWidth: 20 },
        2: { cellWidth: 25 },
        3: { cellWidth: 'auto' }
      }
    })
  }

  // Anomaly 4
  if (data.anomali_4_keyword_jarang_grade4.length > 0) {
    doc.addPage()
    yPos = 20
    doc.setFontSize(12)
    doc.setFont(undefined, 'bold')
    doc.text('Anomali 4: Keyword Jarang di Grade 4', 14, yPos)
    yPos += 8

    const anomaly4Data = data.anomali_4_keyword_jarang_grade4.map(kw => [
      kw.keyword,
      kw.frekuensi,
      `${kw.persen_dokumen_grade4}%`
    ])

    doc.autoTable({
      startY: yPos,
      head: [['Keyword', 'Frekuensi', '% Dokumen Grade 4']],
      body: anomaly4Data,
      theme: 'grid',
      headStyles: { fillColor: [139, 92, 246] },
      margin: { left: 14, right: 14 },
    })
  }

  // Anomaly 5
  if (data.anomali_5_keyword_gap?.length > 0) {
    doc.addPage()
    yPos = 20
    doc.setFontSize(12)
    doc.setFont(undefined, 'bold')
    doc.text('Anomali 5: Kandidat Keyword Baru', 14, yPos)
    yPos += 8

    const anomaly5Data = data.anomali_5_keyword_gap.map(item => [
      item.frasa,
      item.frekuensi,
      item.saran
    ])

    doc.autoTable({
      startY: yPos,
      head: [['Frasa', 'Frekuensi', 'Saran']],
      body: anomaly5Data,
      theme: 'grid',
      headStyles: { fillColor: [16, 185, 129] },
      margin: { left: 14, right: 14 },
      columnStyles: {
        0: { cellWidth: 50 },
        1: { cellWidth: 30 },
        2: { cellWidth: 'auto' }
      }
    })
  }

  // Save PDF
  doc.save(`Laporan_Anomali_DLI_${new Date().getTime()}.pdf`)
}

// Export to Word
export const exportToWord = async (data, t) => {
  const r = data.ringkasan

  const doc = new Document({
    sections: [{
      properties: {},
      children: [
        // Title
        new Paragraph({
          text: 'Laporan Anomali DLI',
          heading: HeadingLevel.HEADING_1,
          alignment: AlignmentType.CENTER,
          spacing: { after: 200 }
        }),
        new Paragraph({
          text: `Tanggal: ${formatDate()}`,
          alignment: AlignmentType.CENTER,
          spacing: { after: 400 }
        }),

        // Summary Section
        new Paragraph({
          text: 'Ringkasan',
          heading: HeadingLevel.HEADING_2,
          spacing: { before: 200, after: 200 }
        }),

        // Summary Table
        new Table({
          width: { size: 100, type: WidthType.PERCENTAGE },
          rows: [
            new TableRow({
              children: [
                new TableCell({ children: [new Paragraph({ text: 'Metrik', bold: true })] }),
                new TableCell({ children: [new Paragraph({ text: 'Nilai', bold: true })] }),
              ]
            }),
            new TableRow({
              children: [
                new TableCell({ children: [new Paragraph('Total Prediksi DLI')] }),
                new TableCell({ children: [new Paragraph(String(r.total_prediksi_dli))] }),
              ]
            }),
            new TableRow({
              children: [
                new TableCell({ children: [new Paragraph('Grade 4')] }),
                new TableCell({ children: [new Paragraph(String(r.grade_4))] }),
              ]
            }),
            new TableRow({
              children: [
                new TableCell({ children: [new Paragraph('Grade 3')] }),
                new TableCell({ children: [new Paragraph(String(r.grade_3))] }),
              ]
            }),
            new TableRow({
              children: [
                new TableCell({ children: [new Paragraph('Grade 2')] }),
                new TableCell({ children: [new Paragraph(String(r.grade_2))] }),
              ]
            }),
            new TableRow({
              children: [
                new TableCell({ children: [new Paragraph('Grade 1')] }),
                new TableCell({ children: [new Paragraph(String(r.grade_1))] }),
              ]
            }),
            new TableRow({
              children: [
                new TableCell({ children: [new Paragraph('Total Anomali 1')] }),
                new TableCell({ children: [new Paragraph(String(r.total_anomali_1))] }),
              ]
            }),
            new TableRow({
              children: [
                new TableCell({ children: [new Paragraph('Total Anomali 2')] }),
                new TableCell({ children: [new Paragraph(String(r.total_anomali_2))] }),
              ]
            }),
            new TableRow({
              children: [
                new TableCell({ children: [new Paragraph('Total Anomali 3')] }),
                new TableCell({ children: [new Paragraph(String(r.total_anomali_3))] }),
              ]
            }),
          ]
        }),

        // Anomaly 1
        ...(data.anomali_1_grade4_aspek_lemah.length > 0 ? [
          new Paragraph({
            text: 'Anomali 1: Grade 4 dengan Aspek Lemah',
            heading: HeadingLevel.HEADING_2,
            spacing: { before: 400, after: 200 },
            pageBreakBefore: true
          }),
          new Table({
            width: { size: 100, type: WidthType.PERCENTAGE },
            rows: [
              new TableRow({
                children: [
                  new TableCell({ children: [new Paragraph({ text: 'File', bold: true })] }),
                  new TableCell({ children: [new Paragraph({ text: 'DLI Score', bold: true })] }),
                  new TableCell({ children: [new Paragraph({ text: 'Aspek Lemah', bold: true })] }),
                ]
              }),
              ...data.anomali_1_grade4_aspek_lemah.map(item => new TableRow({
                children: [
                  new TableCell({ children: [new Paragraph(item.file)] }),
                  new TableCell({ children: [new Paragraph(`${item.dli_score?.toFixed(1)}%`)] }),
                  new TableCell({ children: [new Paragraph(
                    Object.entries(item.weak_aspects).map(([k, v]) => `${k}: ${v?.toFixed(1)}%`).join(', ')
                  )] }),
                ]
              }))
            ]
          })
        ] : []),

        // Anomaly 2
        ...(data.anomali_2_grade1_aspek_kuat.length > 0 ? [
          new Paragraph({
            text: 'Anomali 2: Grade 1 dengan Aspek Kuat',
            heading: HeadingLevel.HEADING_2,
            spacing: { before: 400, after: 200 },
            pageBreakBefore: true
          }),
          new Table({
            width: { size: 100, type: WidthType.PERCENTAGE },
            rows: [
              new TableRow({
                children: [
                  new TableCell({ children: [new Paragraph({ text: 'File', bold: true })] }),
                  new TableCell({ children: [new Paragraph({ text: 'DLI Score', bold: true })] }),
                  new TableCell({ children: [new Paragraph({ text: 'Aspek Kuat', bold: true })] }),
                ]
              }),
              ...data.anomali_2_grade1_aspek_kuat.map(item => new TableRow({
                children: [
                  new TableCell({ children: [new Paragraph(item.file)] }),
                  new TableCell({ children: [new Paragraph(`${item.dli_score?.toFixed(1)}%`)] }),
                  new TableCell({ children: [new Paragraph(
                    Object.entries(item.strong_aspects).map(([k, v]) => `${k}: ${v?.toFixed(1)}%`).join(', ')
                  )] }),
                ]
              }))
            ]
          })
        ] : []),

        // Anomaly 3
        ...(data.anomali_3_grade23_aspek_sangat_kuat.length > 0 ? [
          new Paragraph({
            text: 'Anomali 3: Grade 2/3 dengan Aspek Sangat Kuat',
            heading: HeadingLevel.HEADING_2,
            spacing: { before: 400, after: 200 },
            pageBreakBefore: true
          }),
          new Table({
            width: { size: 100, type: WidthType.PERCENTAGE },
            rows: [
              new TableRow({
                children: [
                  new TableCell({ children: [new Paragraph({ text: 'File', bold: true })] }),
                  new TableCell({ children: [new Paragraph({ text: 'Grade', bold: true })] }),
                  new TableCell({ children: [new Paragraph({ text: 'DLI Score', bold: true })] }),
                  new TableCell({ children: [new Paragraph({ text: 'Aspek Sangat Kuat', bold: true })] }),
                ]
              }),
              ...data.anomali_3_grade23_aspek_sangat_kuat.map(item => new TableRow({
                children: [
                  new TableCell({ children: [new Paragraph(item.file)] }),
                  new TableCell({ children: [new Paragraph(`Grade ${item.grade}`)] }),
                  new TableCell({ children: [new Paragraph(`${item.dli_score?.toFixed(1)}%`)] }),
                  new TableCell({ children: [new Paragraph(
                    Object.entries(item.very_strong_aspects).map(([k, v]) => `${k}: ${v?.toFixed(1)}%`).join(', ')
                  )] }),
                ]
              }))
            ]
          })
        ] : []),

        // Anomaly 4
        ...(data.anomali_4_keyword_jarang_grade4.length > 0 ? [
          new Paragraph({
            text: 'Anomali 4: Keyword Jarang di Grade 4',
            heading: HeadingLevel.HEADING_2,
            spacing: { before: 400, after: 200 },
            pageBreakBefore: true
          }),
          new Table({
            width: { size: 100, type: WidthType.PERCENTAGE },
            rows: [
              new TableRow({
                children: [
                  new TableCell({ children: [new Paragraph({ text: 'Keyword', bold: true })] }),
                  new TableCell({ children: [new Paragraph({ text: 'Frekuensi', bold: true })] }),
                  new TableCell({ children: [new Paragraph({ text: '% Dokumen Grade 4', bold: true })] }),
                ]
              }),
              ...data.anomali_4_keyword_jarang_grade4.map(kw => new TableRow({
                children: [
                  new TableCell({ children: [new Paragraph(kw.keyword)] }),
                  new TableCell({ children: [new Paragraph(String(kw.frekuensi))] }),
                  new TableCell({ children: [new Paragraph(`${kw.persen_dokumen_grade4}%`)] }),
                ]
              }))
            ]
          })
        ] : []),

        // Anomaly 5
        ...(data.anomali_5_keyword_gap?.length > 0 ? [
          new Paragraph({
            text: 'Anomali 5: Kandidat Keyword Baru',
            heading: HeadingLevel.HEADING_2,
            spacing: { before: 400, after: 200 },
            pageBreakBefore: true
          }),
          new Table({
            width: { size: 100, type: WidthType.PERCENTAGE },
            rows: [
              new TableRow({
                children: [
                  new TableCell({ children: [new Paragraph({ text: 'Frasa', bold: true })] }),
                  new TableCell({ children: [new Paragraph({ text: 'Frekuensi', bold: true })] }),
                  new TableCell({ children: [new Paragraph({ text: 'Saran', bold: true })] }),
                ]
              }),
              ...data.anomali_5_keyword_gap.map(item => new TableRow({
                children: [
                  new TableCell({ children: [new Paragraph(item.frasa)] }),
                  new TableCell({ children: [new Paragraph(String(item.frekuensi))] }),
                  new TableCell({ children: [new Paragraph(item.saran)] }),
                ]
              }))
            ]
          })
        ] : []),
      ]
    }]
  })

  // Generate and save
  const blob = await Packer.toBlob(doc)
  saveAs(blob, `Laporan_Anomali_DLI_${new Date().getTime()}.docx`)
}
