import os

from jinja2 import Environment, FileSystemLoader


def render_dashboard(result, png_paths, out_html="site/index.html") -> str:
    env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")))
    tmpl = env.get_template("dashboard.html.j2")
    html = tmpl.render(r=result, pngs=png_paths)
    os.makedirs(os.path.dirname(out_html) or ".", exist_ok=True)
    with open(out_html, "w") as f:
        f.write(html)
    return out_html
