import os
import shutil
import subprocess


def build_markdown(result, png_paths, out_md) -> str:
    lines = [f"# Oracle Dynamic Valuation — {result['quarter']}", "",
             f"- Target: ${result['target']:.2f}",
             f"- Probability-weighted: ${result['pw_price']:.2f}",
             f"- Expected return: {result['expected_return'] * 100:.1f}%",
             f"- alpha: {result['alpha']:.2f}  CEI: {result.get('cei') or 0:.2f} ({result['regime']})",
             f"- M_Neo: {result['m_neo']:.1f}x  Q: {result['q']:.2f}", ""]
    for k, v in png_paths.items():
        lines.append(f"![{k}]({v})")
    os.makedirs(os.path.dirname(out_md) or ".", exist_ok=True)
    with open(out_md, "w") as f:
        f.write("\n".join(lines))
    return out_md


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
