import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


def _save(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_sotp(result, path):
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.bar(["Legacy"], [result["ev_legacy"]], label="Legacy")
    ax.bar(["OCI"], [result["ev_oci"]], label="OCI")
    ax.set_ylabel("EV ($M)")
    ax.legend()
    return _save(fig, path)


def plot_sensitivity(result, path):
    grid = np.array(result["sensitivity"])
    axes = result["sensitivity_axes"]
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(grid, aspect="auto", origin="lower", cmap="viridis")
    ax.set_xticks(range(len(axes["mneo"])))
    ax.set_xticklabels(axes["mneo"])
    ax.set_yticks(range(len(axes["growth"])))
    ax.set_yticklabels(axes["growth"])
    ax.set_xlabel("Neo multiple")
    ax.set_ylabel("OCI growth mult")
    fig.colorbar(im, ax=ax, label="Target $")
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            ax.text(j, i, f"{grid[i, j]:.0f}", ha="center", va="center", color="w", fontsize=7)
    return _save(fig, path)


def plot_scenarios(result, path):
    fig, ax = plt.subplots(figsize=(4, 4))
    names = list(result["scenarios"])
    ax.bar(names, [result["scenarios"][n] for n in names])
    ax.axhline(result["current_price"], linestyle="--")
    ax.set_ylabel("Target $")
    return _save(fig, path)


def plot_alpha_cei(result, path):
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.barh(["alpha", "CEI"], [result["alpha"], (result["cei"] or 0.0)])
    ax.set_xlim(0, max(1.2, (result["cei"] or 0) * 1.1))
    return _save(fig, path)


def plot_event_box(window, target, bear, bull, path):
    fig, ax = plt.subplots(figsize=(6, 4))
    for _, r in window.iterrows():
        color = "green" if r["close"] >= r["open"] else "red"
        ax.plot([r["t"], r["t"]], [r["low"], r["high"]], color=color, linewidth=0.8)
        ax.plot([r["t"], r["t"]], [min(r["open"], r["close"]), max(r["open"], r["close"])],
                color=color, linewidth=4)
    ax.axhline(target, linestyle="-", label="target")
    ax.axhspan(min(bear, bull), max(bear, bull), alpha=0.15, label="Bear-Bull")
    ax.axvline(0, linestyle=":")
    ax.set_xlabel("trading day vs earnings")
    ax.set_ylabel("price $")
    ax.legend()
    return _save(fig, path)
