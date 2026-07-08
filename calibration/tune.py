def ewma(errors: list, lam: float) -> float:
    num = den = 0.0
    for i, e in enumerate(reversed(errors)):   # i=0 is most recent
        w = lam ** (i + 1)
        num += w * e
        den += w
    return num / den if den else 0.0


def propose_m_neo(current_m_neo: float, signed_errors: list, cfg: dict):
    log = {"before": current_m_neo, "after": current_m_neo, "ewma": None,
           "step_pct": 0.0, "applied": False, "reason": ""}
    if len(signed_errors) < cfg["min_quarters"]:
        log["reason"] = f"need >= {cfg['min_quarters']} quarters, have {len(signed_errors)}"
        return current_m_neo, log
    e = ewma(signed_errors, cfg["ewma_lambda"])
    # model too high (e>0) -> lower multiple; cap magnitude at max_step_pct
    step = max(-cfg["max_step_pct"], min(cfg["max_step_pct"], -e))
    new = current_m_neo * (1 + step)
    new = max(cfg["m_neo_hard_min"], min(cfg["m_neo_hard_max"], new))
    log.update(ewma=e, step_pct=step, after=new, applied=True,
               reason="bounded EWMA feedback on systematic error")
    return new, log
