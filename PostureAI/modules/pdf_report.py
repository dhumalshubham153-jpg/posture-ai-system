import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image
from reportlab.lib.enums import TA_CENTER

class PDFReportGenerator:

    def __init__(self):
        os.makedirs('reports', exist_ok=True)

    def generate(self, features, result, risk, recommendations,
                 as_risk=None, filepath=None, snapshot_paths=None):

        if filepath is None:
            ts       = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = f'reports/posture_report_{ts}.pdf'

        doc   = SimpleDocTemplate(filepath, pagesize=A4,
                                  leftMargin=20*mm, rightMargin=20*mm,
                                  topMargin=20*mm, bottomMargin=20*mm)
        styles = getSampleStyleSheet()
        story  = []

        title_style = ParagraphStyle('T', parent=styles['Title'],
                                     fontSize=22, textColor=colors.HexColor('#00c97a'), spaceAfter=4)
        h2_style    = ParagraphStyle('H2', parent=styles['Heading2'],
                                     fontSize=13, textColor=colors.HexColor('#00c97a'),
                                     spaceBefore=12, spaceAfter=4)
        normal      = ParagraphStyle('N', parent=styles['Normal'],
                                     fontSize=10, textColor=colors.HexColor('#334155'))
        center      = ParagraphStyle('C', parent=normal, alignment=TA_CENTER)

        # ── Header ─────────────────────────────────────────────────────────
        story.append(Paragraph("PostureAI Report", title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y %H:%M')}", normal))
        story.append(HRFlowable(width="100%", thickness=1,
                                color=colors.HexColor('#00c97a'), spaceAfter=10))

        # ── Captured Snapshots ──────────────────────────────────────────────
        if snapshot_paths:
            valid_snaps = [p for p in snapshot_paths if p and os.path.exists(p)]
            if valid_snaps:
                story.append(Paragraph("Captured Posture Snapshots", h2_style))
                story.append(Spacer(1, 4))

                # Show up to 3 snapshots side by side
                img_data = []
                labels   = []
                sides    = ["FRONT", "LEFT SIDE", "RIGHT SIDE"]

                for i, snap_path in enumerate(valid_snaps[:3]):
                    try:
                        img = Image(snap_path, width=55*mm, height=45*mm)
                        img_data.append(img)
                        side = sides[i] if i < len(sides) else f"Snapshot {i+1}"
                        labels.append(Paragraph(side, center))
                    except Exception as e:
                        print(f"Snapshot error: {e}")

                if img_data:
                    # Images row
                    img_table = Table([img_data], colWidths=[60*mm]*len(img_data))
                    img_table.setStyle(TableStyle([
                        ('ALIGN',   (0,0), (-1,-1), 'CENTER'),
                        ('VALIGN',  (0,0), (-1,-1), 'MIDDLE'),
                        ('PADDING', (0,0), (-1,-1), 4),
                    ]))
                    story.append(img_table)

                    # Labels row
                    label_table = Table([labels], colWidths=[60*mm]*len(labels))
                    label_table.setStyle(TableStyle([
                        ('ALIGN',   (0,0), (-1,-1), 'CENTER'),
                        ('FONTSIZE',(0,0), (-1,-1), 9),
                        ('TEXTCOLOR',(0,0),(-1,-1), colors.HexColor('#475569')),
                    ]))
                    story.append(label_table)
                    story.append(Spacer(1, 8))

        # ── Posture Score ───────────────────────────────────────────────────
        if result:
            story.append(Paragraph("Posture Score Summary", h2_style))
            score = result.get('score', 0)
            clr   = '#00c97a' if score >= 75 else '#f59e0b' if score >= 50 else '#ef4444'

            score_data = [
                ['Metric',          'Value'],
                ['Posture Score',   f"{score}/100"],
                ['Classification',  result.get('classification', 'N/A')],
            ]
            if risk:
                score_data.append(['Spinal Risk Score', f"{risk.get('risk_score', 0)}/100"])
                score_data.append(['Risk Severity',     risk.get('severity', 'N/A')])

            t = Table(score_data, colWidths=[80*mm, 80*mm])
            t.setStyle(TableStyle([
                ('BACKGROUND',    (0,0), (-1,0), colors.HexColor('#0f172a')),
                ('TEXTCOLOR',     (0,0), (-1,0), colors.HexColor('#00c97a')),
                ('FONTSIZE',      (0,0), (-1,-1), 10),
                ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
                ('ROWBACKGROUNDS',(0,1), (-1,-1),
                 [colors.HexColor('#f8fafc'), colors.HexColor('#f1f5f9')]),
                ('GRID',          (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
                ('PADDING',       (0,0), (-1,-1), 8),
            ]))
            story.append(t)

        # ── Feature Measurements ────────────────────────────────────────────
        if features:
            story.append(Paragraph("Body Measurements", h2_style))
            thresholds = {
                'neck_forward_angle'     : 15,
                'shoulder_slope'         : 10,
                'rounded_shoulder_angle' : 150,
                'pelvic_tilt'            : 10,
                'spine_deviation'        : 20,
            }
            feat_data = [['Measurement', 'Value', 'Status']]
            for k, v in features.items():
                label  = k.replace('_', ' ').title()
                value  = f"{v:.1f}" if v is not None else 'N/A'
                t      = thresholds.get(k, 0)
                if v is None:
                    status = 'Not Detected'
                elif k == 'rounded_shoulder_angle':
                    status = 'Good' if v >= t else 'Needs Attention'
                else:
                    status = 'Good' if v <= t else 'Needs Attention'
                feat_data.append([label, value, status])

            ft = Table(feat_data, colWidths=[70*mm, 50*mm, 50*mm])
            ft.setStyle(TableStyle([
                ('BACKGROUND',    (0,0), (-1,0), colors.HexColor('#0f172a')),
                ('TEXTCOLOR',     (0,0), (-1,0), colors.HexColor('#00c97a')),
                ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE',      (0,0), (-1,-1), 10),
                ('ROWBACKGROUNDS',(0,1), (-1,-1),
                 [colors.HexColor('#f8fafc'), colors.HexColor('#f1f5f9')]),
                ('GRID',          (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
                ('PADDING',       (0,0), (-1,-1), 7),
            ]))
            story.append(ft)

        # ── Exercise Recommendations ─────────────────────────────────────────
        if recommendations:
            story.append(Paragraph("Recommended Exercises", h2_style))
            ex_data = [['Exercise', 'Issue', 'Sets', 'Reps', 'Hold']]
            seen    = set()
            for r in recommendations:
                if r['exercise'] not in seen:
                    seen.add(r['exercise'])
                    ex_data.append([
                        r['exercise'], r['issue'],
                        str(r['sets']), str(r['reps']), f"{r['hold_secs']}s"
                    ])

            et = Table(ex_data, colWidths=[50*mm, 50*mm, 20*mm, 20*mm, 25*mm])
            et.setStyle(TableStyle([
                ('BACKGROUND',    (0,0), (-1,0), colors.HexColor('#0f172a')),
                ('TEXTCOLOR',     (0,0), (-1,0), colors.HexColor('#00c97a')),
                ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE',      (0,0), (-1,-1), 9),
                ('ROWBACKGROUNDS',(0,1), (-1,-1),
                 [colors.HexColor('#f8fafc'), colors.HexColor('#f1f5f9')]),
                ('GRID',          (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
                ('PADDING',       (0,0), (-1,-1), 7),
            ]))
            story.append(et)

        # ── Footer ──────────────────────────────────────────────────────────
        story.append(Spacer(1, 16))
        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=colors.HexColor('#e2e8f0')))
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            "This report is generated by PostureAI. Consult a physiotherapist for medical advice.",
            ParagraphStyle('footer', parent=normal, fontSize=8,
                           textColor=colors.HexColor('#94a3b8'), alignment=TA_CENTER)
        ))

        doc.build(story)
        print(f"PDF saved: {filepath}")
        return filepath