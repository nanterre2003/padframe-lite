import json
import re
from typing import Optional

from .invariants import validate_invariants, TEXT_MATERIAL_INVARIANTS, TEXT_MATERIAL_AUTO_FIX


BRAND_CORRECTIONS = {
    "cloud": "Claude",
    "Cloud": "Claude",
    "clouds": "Claude",
    "Clouds": "Claude",
    "CLOUD": "CLAUDE",
    "clear": "Claude",
    "Clear": "Claude",
    "crowd": "Claude",
    "Crowd": "Claude",
    "克拉奧": "Claude",
    "克勞德": "Claude",
    "可好": "Claude",
    "扣的": "Code",
    "迪bug": "Debug",
    "迪Bug": "Debug",
    "地bug": "Debug",
    "地Bug": "Debug",
    "mybrand": "MyBrand",
    "MYBRAND": "MyBrand",
    "deductions": "Code",
    "deduction": "Code",
    "NetEase": "a domain",
    "net ease": "a domain",
    "RN的動畫": "Render 的動畫",
    "RN 的": "Render 的",
    "rn 的": "Render 的",
    "RN animation": "Render animation",
    "RN animations": "Render animations",
}

CHINESE_HOMOPHONE_CORRECTIONS = {
    "網易": "網域",
    "加過網站": "架過網站",
    "從無到有磕": "從無到有刻",
    "見拜拜": "見 掰掰",
}

PHRASE_CORRECTIONS = {
    "那個體驗非常完整": "整個體驗非常完整",
}


def apply_subtitle_corrections(
    draft: dict,
    extra_corrections: Optional[dict] = None,
    verbose: bool = True,
    use_builtin_corrections: bool = False,
) -> dict:
    """M69 — Apply subtitle corrections to all text materials."""
    all_corrections = []
    if use_builtin_corrections:
        all_corrections.extend([(k, v, "brand") for k, v in BRAND_CORRECTIONS.items()])
        all_corrections.extend([(k, v, "chinese") for k, v in CHINESE_HOMOPHONE_CORRECTIONS.items()])
        all_corrections.extend([(k, v, "phrase") for k, v in PHRASE_CORRECTIONS.items()])
    if extra_corrections:
        all_corrections.extend([(k, v, "extra") for k, v in extra_corrections.items()])

    all_corrections.sort(key=lambda x: -len(x[0]))

    texts = draft.get("materials", {}).get("texts", [])
    changes = []
    fixes_per_kind = {"brand": 0, "chinese": 0, "phrase": 0, "extra": 0}

    @validate_invariants(
        invariants=TEXT_MATERIAL_INVARIANTS,
        auto_fix=TEXT_MATERIAL_AUTO_FIX,
        on_violation="warn",
    )
    def _mutate_one_text(co: dict, corrections_list: list, idx: int) -> dict:
        """Apply correction list to co["text"] in-place."""
        text = co.get("text", "")
        orig_iter = text
        for wrong, right, kind in corrections_list:
            if wrong.isascii() and wrong.replace(" ", "").isalnum():
                new_text, n = re.subn(rf"\b{re.escape(wrong)}\b", right, text)
                if n == 0:
                    continue
                text = new_text
            elif wrong in text:
                text = text.replace(wrong, right)
            else:
                continue
            fixes_per_kind[kind] += 1
            changes.append((idx, orig_iter, text, kind, wrong, right))
            if verbose:
                print(f'  [{idx:3}] {kind}: {wrong!r} → {right!r}')
                print(f'        BEFORE: {orig_iter[:80]}')
                print(f'        AFTER:  {text[:80]}')
            orig_iter = text
        co["text"] = text
        return co

    for i, t in enumerate(texts):
        try:
            co = json.loads(t.get("content", "{}"))
        except json.JSONDecodeError:
            continue
        if not co.get("text"):
            continue
        text_before = co.get("text", "")

        _mutate_one_text(co, all_corrections, i)

        if co.get("text", "") != text_before:
            t["content"] = json.dumps(co, ensure_ascii=False, separators=(",", ":"))

    return {
        "total_fixes": len(changes),
        "fixes_per_kind": fixes_per_kind,
        "changes": changes,
    }


def scan_potential_errors(draft: dict) -> dict:
    """Scan for likely AI errors without modifying."""
    suspect_patterns = [
        (r"\bcloud\b", "→ likely Claude"),
        (r"\bclouds\b", "→ likely Claude"),
        (r"\bclear\b", "→ likely Claude"),
        (r"\bcrowd\b", "→ likely Claude"),
        (r"\bstudio\b", "→ likely Studio (case)"),
        (r"\bRN\b", "→ likely Render"),
        (r"扣的", "→ likely Code"),
        (r"網易", "→ likely 網域"),
        (r"克[拉勞]奧?", "→ likely Claude"),
        (r"可好", "→ likely Claude"),
        (r"加過", "→ likely 架過"),
        (r"迪\s*[bB]ug", "→ likely Debug"),
        (r"拜拜", "→ likely 掰掰"),
        (r"磕出", "→ likely 刻出"),
    ]

    suspects = []
    texts = draft.get("materials", {}).get("texts", [])
    for i, t in enumerate(texts):
        try:
            text = json.loads(t.get("content", "{}")).get("text", "")
        except json.JSONDecodeError:
            continue
        if not text:
            continue
        for pat, note in suspect_patterns:
            if re.search(pat, text, re.IGNORECASE):
                suspects.append({"text_idx": i, "text": text, "pattern": pat, "note": note})

    return {"total_suspects": len(suspects), "suspects": suspects}
