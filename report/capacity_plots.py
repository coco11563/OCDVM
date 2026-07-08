"""Plots for the bottom-up MW-capacity cross-check. Titleless, matplotlib Agg."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


def _save(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_capacity_path(cap, note_new_oci, prior_oci, path):
    """Prior OCI + modeled new OCI vs the note's headline new OCI."""
    fig, ax = plt.subplots(figsize=(5, 4))
    b = 1000.0
    ax.bar("FY prior", prior_oci / b, color="#9bb7d4", label="prior OCI")
    ax.bar("FY next\n(modeled)", prior_oci / b, color="#9bb7d4")
    ax.bar("FY next\n(modeled)", cap.new_oci_revenue / b, bottom=prior_oci / b,
           color="#2e7d32", label="new OCI (util+haircut)")
    if note_new_oci:
        ax.bar("FY next\n(note)", prior_oci / b, color="#9bb7d4")
        ax.bar("FY next\n(note)", note_new_oci / b, bottom=prior_oci / b,
               color="#d1495b", label="new OCI (note headline)")
    ax.set_ylabel("OCI revenue ($B)")
    ax.legend(fontsize=7)
    return _save(fig, path)


def _heatmap(ax, grid, cost_axis, rev_axis, fmt, cmap, mark_cost=None, mark_rev=None):
    im = ax.imshow(grid, aspect="auto", origin="lower", cmap=cmap)
    ax.set_xticks(range(len(rev_axis)))
    ax.set_xticklabels(rev_axis)
    ax.set_yticks(range(len(cost_axis)))
    ax.set_yticklabels(cost_axis)
    ax.set_xlabel("revenue $/MW/yr")
    ax.set_ylabel("build cost $/MW")
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            ax.text(j, i, fmt(grid[i, j]), ha="center", va="center", color="k", fontsize=7)
    if mark_cost in cost_axis and mark_rev in rev_axis:
        ax.add_patch(plt.Rectangle((rev_axis.index(mark_rev) - 0.5, cost_axis.index(mark_cost) - 0.5),
                                   1, 1, fill=False, edgecolor="red", lw=2))
    return im


def plot_roic_heatmap(cost_axis, rev_axis, grid, path, mark=(46.0, 13.5)):
    fig, ax = plt.subplots(figsize=(5, 4))
    im = _heatmap(ax, grid * 100, list(cost_axis), list(rev_axis),
                  lambda v: f"{v:.0f}%", "RdYlGn", mark[0], mark[1])
    fig.colorbar(im, ax=ax, label="pre-tax ROIC %")
    return _save(fig, path)


def plot_cei_heatmap(cost_axis, rev_axis, grid, path, mark=(46.0, 13.5)):
    fig, ax = plt.subplots(figsize=(5, 4))
    im = _heatmap(ax, grid, list(cost_axis), list(rev_axis),
                  lambda v: f"{v:.2f}", "coolwarm", mark[0], mark[1])
    fig.colorbar(im, ax=ax, label="projected CEI (>1 → hyperscaler)")
    return _save(fig, path)
