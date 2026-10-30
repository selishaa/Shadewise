"""
Deterministic foundation shade matcher (Milestone C).

Rules of the road:
- Uses only catalog metadata the human already verified.
- Never invents shades, depths, or accuracy percentages.
- Excludes ShadeWise Demo / illustrative rows even if recommendation_eligible.
- Conservative comparisons — brand labels are not calibrated numbers.
- Returns no match when evidence is too thin to justify a suggestion.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

from app.models.catalog import DepthFamily, FoundationShade, UndertoneFamily
from app.models.matching import (
    MatchShadeRequest,
    MatchShadeResponse,
    ShadeMatchCandidate,
)

DEPTH_ORDER: Tuple[DepthFamily, ...] = ("fair", "light", "medium", "tan", "deep")
DEPTH_RANK = {name: index for index, name in enumerate(DEPTH_ORDER)}

EXCLUDED_BRANDS = frozenset({"shadewise demo"})
MAX_RECOMMENDATIONS = 3

GLOBAL_LIMITATIONS = [
    "Recommendations use brand-reported catalog labels only — not calibrated measurements.",
    "Catalog metadata verification is not proof that a shade will match your skin.",
    "Matching accuracy has not been wear-validated for these suggestions.",
    "At most a few nearby shades in one product line are available in this catalog.",
]


@dataclass(frozen=True)
class _ScoredCandidate:
    shade: FoundationShade
    undertone_score: int
    depth_score: int
    same_product: bool
    reasons: Tuple[str, ...]
    limitations: Tuple[str, ...]

    def sort_key(self) -> Tuple:
        # Higher scores first; same-product preferred; stable tie-breakers.
        return (
            0 if self.same_product else 1,
            -self.undertone_score,
            -self.depth_score,
            self.shade.brand.casefold(),
            self.shade.product.casefold(),
            self.shade.shade_name.casefold(),
            self.shade.id.casefold(),
        )


def is_matcher_candidate(shade: FoundationShade) -> bool:
    """Real, metadata-trusted rows only — never Demo / illustrative / estimated."""
    if shade.brand.casefold() in EXCLUDED_BRANDS:
        return False
    if shade.verification_status == "illustrative":
        return False
    if shade.metadata_verification_status != "source_checked":
        return False
    if shade.verification_status not in {"brand_verified", "independently_measured"}:
        return False
    if shade.matching_accuracy_status == "insufficient_evidence":
        return False
    return True


def find_current_shade(
    catalog: Sequence[FoundationShade],
    request: MatchShadeRequest,
) -> Optional[FoundationShade]:
    """Locate the user's current shade when brand/product/shade identify it uniquely."""
    if not request.shade_name and not request.shade_code:
        return None

    candidates = list(catalog)

    if request.brand:
        needle = request.brand.casefold()
        candidates = [s for s in candidates if s.brand.casefold() == needle]
    if request.product:
        needle = request.product.casefold()
        candidates = [s for s in candidates if s.product.casefold() == needle]

    shade_needle = (request.shade_name or "").casefold()
    code_needle = (request.shade_code or "").casefold()

    matches: List[FoundationShade] = []
    for shade in candidates:
        name_hit = bool(shade_needle) and shade.shade_name.casefold() == shade_needle
        code_hit = bool(code_needle) and (shade.shade_code or "").casefold() == code_needle
        # Also allow shade_name field to match shade_code (users often type L5 / M1).
        cross_hit = bool(shade_needle) and (shade.shade_code or "").casefold() == shade_needle
        if name_hit or code_hit or cross_hit:
            matches.append(shade)

    if len(matches) == 1:
        return matches[0]
    return None


def _effective_depth(shade: FoundationShade) -> Optional[DepthFamily]:
    """Prefer independent measurement when present; otherwise brand-reported only."""
    return shade.independent_depth or shade.brand_reported_depth


def _effective_undertone(shade: FoundationShade) -> Optional[UndertoneFamily]:
    return shade.independent_undertone or shade.brand_reported_undertone


def _undertone_preference(
    issue: str, candidate_undertone: Optional[UndertoneFamily]
) -> Optional[int]:
    """
    Score undertone fit. None means disqualified for this issue.

    Conservative: when the user has a clear undertone complaint, do not suggest
    shades that repeat the same problem undertone.
    """
    if candidate_undertone is None:
        return None

    if issue == "too_warm":
        # Prefer cooler; neutral ok; olive sometimes helps orange cast; reject warm.
        ranking = {"cool": 3, "neutral": 2, "olive": 1, "warm": None}
        return ranking.get(candidate_undertone)

    if issue == "too_cool":
        ranking = {"warm": 3, "neutral": 2, "olive": 1, "cool": None}
        return ranking.get(candidate_undertone)

    if issue == "none":
        # Prefer keeping undertone; we score equality later against current.
        return 1

    # unsure — weak preference only; still need some undertone present to compare.
    return 0


def _depth_preference(
    feedback: str,
    current_depth: Optional[DepthFamily],
    candidate_depth: Optional[DepthFamily],
) -> Optional[int]:
    """
    Score depth fit. None means disqualified.

    Without a known current depth, depth-direction feedback cannot be applied.
    """
    if feedback == "unsure":
        if candidate_depth is None:
            return None
        return 0

    if feedback == "correct":
        if current_depth is None or candidate_depth is None:
            # Cannot confirm "same depth" without both labels.
            return None
        # Exact family match only — brand labels are not calibrated steps.
        if candidate_depth == current_depth:
            return 2
        return None

    # too_light → need deeper; too_dark → need lighter
    if current_depth is None or candidate_depth is None:
        return None

    cur = DEPTH_RANK[current_depth]
    cand = DEPTH_RANK[candidate_depth]

    if feedback == "too_light":
        if cand > cur:
            return 3 if cand == cur + 1 else 1
        return None

    if feedback == "too_dark":
        if cand < cur:
            return 3 if cand == cur - 1 else 1
        return None

    return None


def _evidence_status(shade: FoundationShade) -> str:
    accuracy = shade.matching_accuracy_status
    return (
        f"Catalog metadata {shade.metadata_verification_status}; "
        f"matching accuracy {accuracy}. "
        "Metadata verification is not proof of match accuracy."
    )


def _build_reasons(
    request: MatchShadeRequest,
    current: Optional[FoundationShade],
    candidate: FoundationShade,
    undertone_score: int,
    depth_score: int,
) -> List[str]:
    reasons: List[str] = []
    cand_depth = _effective_depth(candidate)
    cand_under = _effective_undertone(candidate)

    if current and current.product.casefold() == candidate.product.casefold():
        reasons.append(
            f"Same product line as your current shade ({candidate.product})."
        )

    if request.undertone_issue == "too_warm" and cand_under:
        reasons.append(
            f"Catalog undertone is '{cand_under}', which is cooler or less warm "
            "than a warm/orange-leaning shade."
        )
    elif request.undertone_issue == "too_cool" and cand_under:
        reasons.append(
            f"Catalog undertone is '{cand_under}', which is warmer or less cool "
            "than a pink/cool-leaning shade."
        )
    elif request.undertone_issue == "none" and current:
        cur_under = _effective_undertone(current)
        if cur_under and cand_under == cur_under:
            reasons.append(
                f"Keeps the same brand-reported undertone ('{cand_under}') as your current shade."
            )

    if request.depth_feedback == "correct" and cand_depth and current:
        cur_depth = _effective_depth(current)
        if cur_depth and cand_depth == cur_depth:
            reasons.append(
                f"Keeps the same brand-reported depth family ('{cand_depth}')."
            )
    elif request.depth_feedback == "too_light" and cand_depth and current:
        reasons.append(
            f"Brand-reported depth '{cand_depth}' is deeper than your current "
            f"'{_effective_depth(current)}' label."
        )
    elif request.depth_feedback == "too_dark" and cand_depth and current:
        reasons.append(
            f"Brand-reported depth '{cand_depth}' is lighter than your current "
            f"'{_effective_depth(current)}' label."
        )

    if undertone_score == 0 and depth_score == 0 and not reasons:
        reasons.append("Included as a nearby catalog candidate with incomplete preference signal.")

    return reasons


def _build_limitations(
    request: MatchShadeRequest,
    current: Optional[FoundationShade],
    candidate: FoundationShade,
) -> List[str]:
    limits: List[str] = [
        "This is a catalog-label comparison only — try shades in person when possible.",
    ]
    if _effective_depth(candidate) is None:
        limits.append(
            f"{candidate.shade_name} has no normalized depth classification in the catalog."
        )
    if current and _effective_depth(current) is None:
        limits.append(
            f"Your current shade ({current.shade_name}) has no normalized depth in the catalog, "
            "so depth comparisons are limited."
        )
    if request.depth_feedback in {"too_light", "too_dark"} and current is None:
        limits.append("Depth direction was applied without a confirmed current catalog shade.")
    if candidate.matching_accuracy_status == "not_evaluated":
        limits.append(
            "No wear-test evidence yet for this recommendation — do not treat it as proven."
        )
    return limits


def score_candidate(
    request: MatchShadeRequest,
    current: Optional[FoundationShade],
    candidate: FoundationShade,
) -> Optional[_ScoredCandidate]:
    if current and candidate.id == current.id:
        return None

    cand_depth = _effective_depth(candidate)
    cand_under = _effective_undertone(candidate)
    current_depth = _effective_depth(current) if current else None
    current_under = _effective_undertone(current) if current else None

    # Undertone scoring
    if request.undertone_issue in {"too_warm", "too_cool"}:
        under_score = _undertone_preference(request.undertone_issue, cand_under)
        if under_score is None:
            return None
    elif request.undertone_issue == "none":
        if current_under is None or cand_under is None:
            return None
        if cand_under != current_under:
            # Strict when user says undertone is fine: keep same label only.
            return None
        under_score = 2
    else:  # unsure
        if cand_under is None:
            return None
        under_score = 0

    # Depth scoring
    if request.depth_feedback == "correct":
        if current is None or current_depth is None:
            # Cannot assert "depth is fine" against unlabeled current.
            return None
        depth_score = _depth_preference("correct", current_depth, cand_depth)
        if depth_score is None:
            return None
    elif request.depth_feedback in {"too_light", "too_dark"}:
        if current is None or current_depth is None:
            return None
        depth_score = _depth_preference(
            request.depth_feedback, current_depth, cand_depth
        )
        if depth_score is None:
            return None
    else:  # unsure
        if cand_depth is None:
            # Still allow undertone-only suggestions when depth feedback is unsure
            # and candidate lacks depth — but only if undertone issue is actionable.
            if request.undertone_issue not in {"too_warm", "too_cool"}:
                return None
            depth_score = 0
        else:
            depth_score = 0

    same_product = bool(
        current
        and current.brand.casefold() == candidate.brand.casefold()
        and current.product.casefold() == candidate.product.casefold()
    )

    # Prefer same brand/product when current is known; still allow other real brands.
    reasons = _build_reasons(request, current, candidate, under_score, depth_score)
    limitations = _build_limitations(request, current, candidate)

    return _ScoredCandidate(
        shade=candidate,
        undertone_score=under_score,
        depth_score=depth_score,
        same_product=same_product,
        reasons=tuple(reasons),
        limitations=tuple(limitations),
    )


def _insufficient_signal_reason(request: MatchShadeRequest) -> Optional[str]:
    """Return an explanation when the request alone cannot support matching."""
    if request.depth_feedback == "unsure" and request.undertone_issue == "unsure":
        return (
            "Need at least one clear depth or undertone signal "
            "(too light/dark/correct, or too warm/cool) before recommending."
        )
    return None


def match_shades(
    request: MatchShadeRequest,
    catalog: Iterable[FoundationShade],
) -> MatchShadeResponse:
    """
    Pure function: request + catalog → up to three recommendations or a no-match.
    """
    catalog_list = list(catalog)
    current = find_current_shade(catalog_list, request)

    early = _insufficient_signal_reason(request)
    if early:
        return MatchShadeResponse(
            matched_current_shade_id=current.id if current else None,
            recommendations=[],
            no_match_reason=early,
            global_limitations=list(GLOBAL_LIMITATIONS),
        )

    # Depth-direction or "depth correct" needs a known current depth.
    needs_current_depth = request.depth_feedback in {
        "too_light",
        "too_dark",
        "correct",
    }
    if needs_current_depth:
        if current is None:
            hint = ""
            if request.shade_name or request.shade_code:
                hint = (
                    f" Shade {request.shade_name or request.shade_code!r} was not found "
                    "as an exact catalog match."
                )
            return MatchShadeResponse(
                matched_current_shade_id=None,
                recommendations=[],
                no_match_reason=(
                    "Depth feedback requires identifying your current shade in the catalog "
                    "so we can compare brand-reported depth labels."
                    + hint
                ),
                global_limitations=list(GLOBAL_LIMITATIONS),
            )
        if _effective_depth(current) is None:
            return MatchShadeResponse(
                matched_current_shade_id=current.id,
                recommendations=[],
                no_match_reason=(
                    f"{current.shade_name} has no normalized depth classification in the catalog, "
                    "so ShadeWise will not invent a depth comparison for "
                    f"depth_feedback={request.depth_feedback!r}."
                ),
                global_limitations=list(GLOBAL_LIMITATIONS),
            )

    # Undertone "none" (keep same) needs current undertone.
    if request.undertone_issue == "none":
        if current is None:
            return MatchShadeResponse(
                matched_current_shade_id=None,
                recommendations=[],
                no_match_reason=(
                    "Keeping undertone the same requires identifying your current shade "
                    "in the catalog."
                ),
                global_limitations=list(GLOBAL_LIMITATIONS),
            )
        if _effective_undertone(current) is None:
            return MatchShadeResponse(
                matched_current_shade_id=current.id,
                recommendations=[],
                no_match_reason=(
                    f"{current.shade_name} has no undertone classification in the catalog, "
                    "so same-undertone filtering cannot run."
                ),
                global_limitations=list(GLOBAL_LIMITATIONS),
            )

    pool = [s for s in catalog_list if is_matcher_candidate(s)]
    scored: List[_ScoredCandidate] = []
    for shade in pool:
        result = score_candidate(request, current, shade)
        if result is not None:
            scored.append(result)

    scored.sort(key=lambda item: item.sort_key())
    top = scored[:MAX_RECOMMENDATIONS]

    if not top:
        reason_parts = [
            "No suitable real catalog shades met the conservative depth/undertone rules."
        ]
        if current:
            reason_parts.append(
                f"Compared from current shade {current.shade_name} "
                f"(depth={_effective_depth(current)!r}, "
                f"undertone={_effective_undertone(current)!r})."
            )
        if request.shade_name and current is None:
            reason_parts.append(
                f"Current shade {request.shade_name!r} was not recognized in the catalog."
            )
        return MatchShadeResponse(
            matched_current_shade_id=current.id if current else None,
            recommendations=[],
            no_match_reason=" ".join(reason_parts),
            global_limitations=list(GLOBAL_LIMITATIONS),
        )

    recommendations = [
        ShadeMatchCandidate(
            catalog_id=item.shade.id,
            brand=item.shade.brand,
            product=item.shade.product,
            shade_name=item.shade.shade_name,
            shade_code=item.shade.shade_code,
            selection_reasons=list(item.reasons),
            limitations=list(item.limitations),
            evidence_status=_evidence_status(item.shade),
        )
        for item in top
    ]

    return MatchShadeResponse(
        matched_current_shade_id=current.id if current else None,
        recommendations=recommendations,
        no_match_reason=None,
        global_limitations=list(GLOBAL_LIMITATIONS),
    )
