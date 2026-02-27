from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, PageBreak
)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
import pandas as pd
import json
from ..systemic.diagnostics import SystemicDiagnostics

class RunPDFBuilder:

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.small_style = ParagraphStyle(
            "small",
            parent=self.styles["Normal"],
            fontSize=8,
            leading=10
        )

    # --------------------------------------------------
    # Safe Table Builder (Auto Landscape)
    # --------------------------------------------------

    def _build_table(self, data):

        col_count = len(data[0])

        # Auto landscape if wide
        if col_count > 7:
            page_size = landscape(A4)
        else:
            page_size = A4

        usable_width = page_size[0] - 80
        col_width = usable_width / col_count
        col_widths = [col_width] * col_count

        wrapped = []
        for row in data:
            wrapped.append([
                Paragraph(str(cell), self.small_style)
                for cell in row
            ])

        table = Table(
            wrapped,
            colWidths=col_widths,
            repeatRows=1
        )

        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        return table, page_size

    # --------------------------------------------------
    # Convert Dict to Table
    # --------------------------------------------------

    def _dict_to_table(self, data_dict):

        rows = [["Field", "Value"]]
        for k, v in data_dict.items():
            if isinstance(v, (dict, list)):
                v = json.dumps(v)
            rows.append([k, v])

        return rows

    # --------------------------------------------------
    # Convert DataFrame / List to Table
    # --------------------------------------------------

    def _object_to_table(self, obj):

        if isinstance(obj, pd.DataFrame):
            if obj.empty:
                return None
            return [obj.columns.tolist()] + obj.values.tolist()

        if isinstance(obj, list):
            if len(obj) == 0:
                return None
            if isinstance(obj[0], dict):
                headers = list(obj[0].keys())
                rows = [headers]
                for item in obj:
                    rows.append([item.get(h) for h in headers])
                return rows

        return None

    # --------------------------------------------------
    # Ranking Section
    # --------------------------------------------------

    def _build_ranking(self, states):

        headers = [
            "Underlying",
            "Gamma",
            "IV",
            "HV",
            "Confidence",
            "Acceleration",
            "SSI",
            "Persistence",
            "Quadrant",
            "Instability"
        ]

        rows = [headers]

        for underlying, state in states.items():

            confidence = state.get("regime_confidence", 0)
            accel = state.get("acceleration_probability", 0)

            ssi = round(0.6 * accel + 0.4 * confidence, 3)
            persistence = round(confidence * (1 - 0.5 * accel), 3)
            instability = round(accel * 100, 1)

            if ssi >= 0.6 and persistence >= 0.6:
                quadrant = "Stable Trend"
            elif ssi >= 0.6:
                quadrant = "Breakout Candidate"
            elif persistence >= 0.6:
                quadrant = "Range Stable"
            else:
                quadrant = "Low Edge"

            rows.append([
                underlying,
                state.get("gamma_surface_regime"),
                state.get("iv"),
                state.get("hv"),
                confidence,
                accel,
                ssi,
                persistence,
                quadrant,
                instability
            ])

        return rows

    # --------------------------------------------------
    # Systemcic risk computation
    # --------------------------------------------------

    def _compute_systemic_risk_index(self, states):

        total_assets = len(states)

        avg_accel = 0
        short_gamma_count = 0
        low_persistence_count = 0
        instability_count = 0

        for state in states.values():

            accel = state.get("acceleration_probability", 0)
            confidence = state.get("regime_confidence", 0)
            persistence = confidence * (1 - 0.5 * accel)

            avg_accel += accel

            if state.get("gamma_surface_regime") == "SHORT_GAMMA":
                short_gamma_count += 1

            if persistence < 0.5:
                low_persistence_count += 1

            instability = state.get("instability_pockets")
            if isinstance(instability, list) and len(instability) > 0:
                instability_count += 1

        avg_accel /= max(total_assets, 1)

        short_gamma_ratio = short_gamma_count / max(total_assets, 1)
        low_persistence_ratio = low_persistence_count / max(total_assets, 1)
        instability_ratio = instability_count / max(total_assets, 1)

        sri = (
                0.35 * avg_accel +
                0.25 * short_gamma_ratio +
                0.20 * low_persistence_ratio +
                0.20 * instability_ratio
        )

        return round(sri, 3), {
            "Average Acceleration": round(avg_accel, 3),
            "Short Gamma Ratio": round(short_gamma_ratio, 3),
            "Low Persistence Ratio": round(low_persistence_ratio, 3),
            "Instability Density": round(instability_ratio, 3)
        }

    # --------------------------------------------------
    # Build PDF
    # --------------------------------------------------

    def build(self, run_payload, output_path):

        states = run_payload["states"]

        elements = []

        # Cover
        elements.append(Paragraph(
            "<b>Multi-Asset Regime Screening Report</b>",
            self.styles["Heading1"]
        ))
        elements.append(Spacer(1, 0.4 * inch))
        elements.append(Paragraph(
            f"Run ID: {run_payload['run_id']}",
            self.styles["Normal"]
        ))
        elements.append(PageBreak())

        # Ranking
        ranking_data = self._build_ranking(states)
        ranking_table, ranking_page_size = self._build_table(ranking_data)

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=ranking_page_size,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        elements.append(Paragraph("<b>Cross-Asset Ranking</b>", self.styles["Heading2"]))
        elements.append(Spacer(1, 0.3 * inch))
        elements.append(ranking_table)
        elements.append(PageBreak())

        # --------------------------------------------------
        # Systemic Risk Index Page
        # --------------------------------------------------

        sri_value, sri_components = self._compute_systemic_risk_index(states)

        elements.append(Paragraph(
            "<b>Systemic Risk Index</b>",
            self.styles["Heading2"]
        ))
        elements.append(Spacer(1, 0.3 * inch))

        elements.append(Paragraph(
            f"<b>SRI Score:</b> {sri_value}",
            self.styles["Normal"]
        ))
        elements.append(Spacer(1, 0.2 * inch))

        # Risk classification
        if sri_value > 0.7:
            risk_label = "HIGH SYSTEMIC RISK"
        elif sri_value > 0.45:
            risk_label = "MODERATE SYSTEMIC RISK"
        else:
            risk_label = "LOW SYSTEMIC RISK"

        elements.append(Paragraph(
            f"<b>Risk Classification:</b> {risk_label}",
            self.styles["Normal"]
        ))
        elements.append(Spacer(1, 0.3 * inch))

        # Components table
        components_table_data = [["Component", "Value"]]
        for k, v in sri_components.items():
            components_table_data.append([k, v])

        components_table, _ = self._build_table(components_table_data)
        elements.append(components_table)
        elements.append(PageBreak())

        systemic = run_payload.get("systemic_metrics", {})
        elements.append(Paragraph(
            "<b>Systemic Diagnostics</b>",
            self.styles["Heading2"]
        ))
        elements.append(Spacer(1, 0.3 * inch))

        diagnostic_table = [
            ["Metric", "Score"],
            ["Systemic Risk Index", systemic.get("systemic_risk_index")],
            ["Gamma Alignment", systemic.get("gamma_alignment")],
            ["Vol Expansion Breadth", systemic.get("vol_expansion_breadth")],
            ["Correlation Shock", systemic.get("correlation_shock")],
            ["Regime Synchronization", systemic.get("regime_sync")]
        ]

        table, _ = self._build_table(diagnostic_table)
        elements.append(table)
        elements.append(PageBreak())



        # Detail per underlying
        for underlying, state in states.items():

            elements.append(Paragraph(
                f"<b>{underlying}</b>",
                self.styles["Heading2"]
            ))
            elements.append(Spacer(1, 0.2 * inch))

            # Main state
            main_table, _ = self._build_table(
                self._dict_to_table(state)
            )
            elements.append(main_table)
            elements.append(Spacer(1, 0.3 * inch))

            # Instability Pockets
            inst_table_data = self._object_to_table(
                state.get("instability_pockets")
            )
            if inst_table_data:
                elements.append(Paragraph("<b>Instability Pockets</b>", self.styles["Heading3"]))
                table, _ = self._build_table(inst_table_data)
                elements.append(table)
                elements.append(Spacer(1, 0.3 * inch))

            # Convexity Traps
            conv_table_data = self._object_to_table(
                state.get("convexity_traps")
            )
            if conv_table_data:
                elements.append(Paragraph("<b>Convexity Traps</b>", self.styles["Heading3"]))
                table, _ = self._build_table(conv_table_data)
                elements.append(table)
                elements.append(Spacer(1, 0.3 * inch))

            # Adaptive Signal
            adaptive = state.get("adaptive_signal")
            if isinstance(adaptive, dict):
                elements.append(Paragraph("<b>Adaptive Signal</b>", self.styles["Heading3"]))
                adaptive_table, _ = self._build_table(
                    self._dict_to_table(adaptive)
                )
                elements.append(adaptive_table)

            elements.append(PageBreak())

        doc.build(elements)

        return output_path