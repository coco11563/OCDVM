import os
import shutil
import subprocess


def build_markdown(result, png_paths, out_md, commentary_md=None) -> str:
    lines = [f"# Oracle Dynamic Valuation — {result['quarter']}", "",
             f"- Target: ${result['target']:.2f}",
             f"- Probability-weighted: ${result['pw_price']:.2f}",
             f"- Expected return: {result['expected_return'] * 100:.1f}%",
             f"- alpha: {result['alpha']:.2f}  CEI: {result.get('cei') or 0:.2f} ({result['regime']})",
             f"- M_Neo: {result['m_neo']:.1f}x  Q: {result['q']:.2f}", ""]
    if commentary_md:
        lines += ["## Interpretation", "", commentary_md, ""]
    lines += ["## Charts", ""]
    for k, v in png_paths.items():
        lines.append(f"![{k}]({v})")
    os.makedirs(os.path.dirname(out_md) or ".", exist_ok=True)
    with open(out_md, "w") as f:
        f.write("\n".join(lines))
    return out_md


_CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
]


def _find_chrome():
    for c in _CHROME_CANDIDATES:
        if os.path.isabs(c):
            if os.path.exists(c):
                return c
        elif shutil.which(c):
            return shutil.which(c)
    return None


def html_to_pdf(html_path, pdf_path):
    """Print the styled dashboard HTML to PDF with headless Chrome (unicode/CSS/images safe)."""
    chrome = _find_chrome()
    if not chrome:
        return None
    src = "file://" + os.path.abspath(html_path)
    try:
        subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        "--virtual-time-budget=3000",
                        f"--print-to-pdf={os.path.abspath(pdf_path)}", src],
                       check=True, capture_output=True, timeout=90)
        return pdf_path if os.path.exists(pdf_path) else None
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print("chrome pdf failed:", e)
        return None


def to_pdf(md_path, pdf_path):
    if shutil.which("pandoc"):
        resource_dir = os.path.dirname(os.path.abspath(md_path)) or "."
        try:
            subprocess.run(["pandoc", md_path, "-o", pdf_path,
                            f"--resource-path={resource_dir}"], check=True)
            return pdf_path
        except subprocess.CalledProcessError as e:
            print("pandoc failed:", e)
    print("pandoc not available; leaving Markdown only:", md_path)
    return None
