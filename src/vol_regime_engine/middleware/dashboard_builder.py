from pathlib import Path
from datetime import datetime


class DashboardBuilder:

    def __init__(self, base_dir="engine_logs"):
        self.base_dir = Path(base_dir)

    # --------------------------------------------------
    # Build Daily Index
    # --------------------------------------------------

    def build_daily_index(self, underlying, date_str):

        day_dir = self.base_dir / underlying / date_str

        html = f"""
        <html>
        <head><title>{underlying} - {date_str}</title></head>
        <body>
        <h1>{underlying} - {date_str}</h1>
        """

        for session in ["intraday", "overnight"]:
            session_dir = day_dir / session

            if session_dir.exists():
                html += f"<h2>{session.capitalize()}</h2><ul>"

                for file in sorted(session_dir.glob("*.html")):
                    rel = file.name
                    html += f'<li><a href="{session}/{rel}">{rel}</a></li>'

                # state_changes subfolder
                change_dir = session_dir / "state_changes"
                if change_dir.exists():
                    html += "<li>State Changes<ul>"
                    for file in sorted(change_dir.glob("*.html")):
                        rel = f"{session}/state_changes/{file.name}"
                        html += f'<li><a href="{rel}">{file.name}</a></li>'
                    html += "</ul></li>"

                html += "</ul>"

        html += "</body></html>"

        (day_dir / "index.html").write_text(html, encoding="utf-8")

    # --------------------------------------------------
    # Build Underlying Dashboard
    # --------------------------------------------------

    def build_underlying_index(self, underlying):

        underlying_dir = self.base_dir / underlying

        html = f"""
        <html>
        <head><title>{underlying} Dashboard</title></head>
        <body>
        <h1>{underlying} Dashboard</h1>
        <ul>
        """

        for day in sorted(underlying_dir.iterdir(), reverse=True):
            if day.is_dir():
                html += f'<li><a href="{day.name}/index.html">{day.name}</a></li>'

        html += "</ul></body></html>"

        (underlying_dir / "index.html").write_text(html, encoding="utf-8")

    # --------------------------------------------------
    # Build Global Dashboard
    # --------------------------------------------------

    def build_global_index(self):

        html = """
        <html>
        <head><title>Volatility Regime Dashboard</title></head>
        <body>
        <h1>Volatility Regime Dashboard</h1>
        <ul>
        """

        for underlying_dir in sorted(self.base_dir.iterdir()):
            if underlying_dir.is_dir():
                html += f'<li><a href="{underlying_dir.name}/index.html">{underlying_dir.name}</a></li>'

        html += "</ul></body></html>"

        (self.base_dir / "index.html").write_text(html, encoding="utf-8")
