# =============================================================================
# EU PROGRESS REPORT — CRITICISM & REFORM DICTIONARY
# =============================================================================
# EPU-style keyword dictionary for scoring EU progress reports.
# Methodology follows Baker, Bloom & Davis (2016): words are counted per chunk,
# normalized per 1,000 words.
#
# Structure mirrors hard/soft obligation split (cf. trade agreement scoring):
#   CRITICISM_HARD  — unambiguous failure/regression language
#   CRITICISM_SOFT  — hedged concern/challenge language
#   REFORM_HARD     — concrete completed achievements
#   REFORM_SOFT     — process/intent/in-progress language
#
# Key derived scores:
#   criticism_hard_p1k, criticism_soft_p1k
#   reform_hard_p1k,    reform_soft_p1k
#   net_criticism       = (criticism_hard_p1k + criticism_soft_p1k)
#                       - (reform_hard_p1k    + reform_soft_p1k)
#   severity_ratio      = criticism_hard_p1k / criticism_soft_p1k
#                         ↑ high = EU is explicitly condemning, not just flagging
#                         (undefined / set to NaN if soft = 0, rare at document level)
#
# HOW TO USE:
#   from dictionary import (CRITICISM_HARD, CRITICISM_SOFT,
#                           REFORM_HARD, REFORM_SOFT, TOPICS)
#
# SCORING: substring match on lowercased text (catches multi-word phrases).
# =============================================================================


# -----------------------------------------------------------------------------
# CRITICISM — HARD
# EU is explicitly calling out failure, regression, or a serious problem.
# These should be rare enough to be meaningful — not bureaucratic filler.
# -----------------------------------------------------------------------------
CRITICISM_HARD = [
    # Failure / non-delivery
    'failed',
    'failure',
    'failing',
    'has not been implemented',
    'have not been implemented',
    'not implemented',
    'non-implementation',

    # Regression / deterioration
    'backsliding',
    'backslide',
    'deterioration',
    'deteriorated',
    'regressed',
    'regression',
    'stagnation',
    'stagnated',
    'standstill',

    # Explicit legal/rights violations
    'violation',
    'violations',
    'breach',
    'breached',
    'impunity',
    'obstruction',
    'obstructed',
    'interference',       # e.g. interference in judiciary

    # Strong inadequacy
    'inadequate',
    'insufficient',
    'insufficiently',
    'absence of',
    'lack of',            # multi-word — more specific than bare 'lack'
    'deficiencies',
    'deficiency',
    'shortcomings',
    'shortcoming',
    'incomplete',
    'incompleteness',

    # Political/structural critique
    'politicisation',
    'politicization',
    'state capture',
    'systemic',           # systemic corruption / systemic problems
    'selective',          # selective justice / selective prosecution
]


# -----------------------------------------------------------------------------
# CRITICISM — SOFT
# EU is flagging concern or noting challenges — hedged, not condemning.
# These are common in EU reports and carry weaker signal individually.
# -----------------------------------------------------------------------------
CRITICISM_SOFT = [
    # Concern / worry language
    'concern',
    'concerns',
    'concerning',
    'worrying',
    'serious concern',

    # Challenge / difficulty
    'challenge',
    'challenges',
    'challenging',
    'difficult',
    'difficulty',

    # Delay / slowness
    'delayed',
    'delay',
    'delays',
    'slow',
    'stalled',

    # Limitation
    'limited',
    'limiting',
    'limited progress',
    'limited results',

    # Persistence of problems
    'persisting',
    'persistent',
    'outstanding',        # e.g. "outstanding issues"
    'remain',             # "challenges remain" — soft signal
    'remains',

    # Generic problem language
    'problem',
    'problems',
    'problematic',
    'issue',
    'issues',
    'risk',
    'risks',

    # Weak obligation / need language
    'need',
    'needs',
    'needed',
    'require',
    'required',
    'requires',
    'must be',            # multi-word: more specific than bare 'must'
    'needs to be',
    'has yet to',
    'have yet to',
]


# -----------------------------------------------------------------------------
# REFORM — HARD
# EU is confirming a concrete, completed achievement.
# These should represent measurable delivery.
# -----------------------------------------------------------------------------
REFORM_HARD = [
    # Legislation / formal steps
    'adopted',
    'adopting',
    'enacted',
    'enacted into law',
    'ratified',
    'transposed',         # EU-specific: transposing directives into national law
    'approved',
    'entered into force',

    # Implementation confirmed
    'implemented',
    'implementing',
    'completed',
    'completion',
    'finalised',
    'finalized',
    'operationalised',
    'operationalized',

    # Establishment of institutions/mechanisms
    'established',
    'establishing',
    'set up',
    'created',
    'launched',

    # Concrete results / achievements
    'achieved',
    'achievement',
    'achieves',
    'accelerated',
    'delivered',
    'consolidated',
    'sustained progress',
    'tangible results',
    'track record',
]


# -----------------------------------------------------------------------------
# REFORM — SOFT
# EU is acknowledging effort or intent without confirming delivery.
# "Working towards" is not the same as "implemented".
# -----------------------------------------------------------------------------
REFORM_SOFT = [
    # Progress language (without completion)
    'progress',
    'progressed',
    'advanced',
    'advances',
    'some progress',
    'good progress',
    'further progress',

    # Improvement (can be partial)
    'improved',
    'improving',
    'improvement',
    'strengthened',
    'strengthening',
    'enhanced',
    'enhance',

    # Positive evaluation (general)
    'effective',
    'effectively',
    'efficient',
    'efficiency',
    'functional',
    'functioning',
    'positive',
    'positively',

    # Effort / steps taken (not confirmed delivery)
    'steps taken',
    'efforts',
    'initiated',
    'underway',
    'ongoing',
    'in progress',
    'working towards',
    'moving towards',
    'seeking to',

    # Generic positive
    'success',
    'successful',
    'successfully',
    'well',               # [WEAK] — "well-functioning" OK, "as well" is noise
    'good',               # [WEAK]
    'better',             # [WEAK]
]


# -----------------------------------------------------------------------------
# CONVENIENCE ALIASES
# For backwards compatibility with existing notebooks that use
# reform_words / criticism_words as flat sets.
# -----------------------------------------------------------------------------
criticism_words = set(CRITICISM_HARD + CRITICISM_SOFT)
reform_words    = set(REFORM_HARD    + REFORM_SOFT)


# -----------------------------------------------------------------------------
# TOPIC DICTIONARIES
# -----------------------------------------------------------------------------
TOPICS = {
    'judiciary': {
        'court', 'courts', 'judicial', 'judge', 'judges', 'judgment', 'judgement',
        'prosecution', 'prosecutor', 'prosecutors', 'trial', 'trials',
        'justice', 'tribunal', 'verdict', 'appeal', 'appeals',
        'conviction', 'acquittal', 'magistrate', 'indictment', 'vetting',
        'supreme court', 'constitutional court', 'rule of law',
    },
    'corruption': {
        'corruption', 'corrupt', 'fraud', 'fraudulent', 'bribery', 'bribe',
        'transparency', 'integrity', 'embezzlement', 'money laundering',
        'conflict of interest', 'anticorruption', 'anti-corruption',
        'illicit', 'misconduct', 'nepotism', 'patronage', 'accountability',
        'asset declaration', 'public procurement',
    },
    'governance': {
        'administration', 'governance', 'public sector', 'civil service',
        'institution', 'institutional', 'parliament', 'parliamentary',
        'executive', 'legislation', 'legislative', 'regulation', 'regulatory',
        'ministry', 'ministries', 'capacity', 'decentralisation', 'decentralization',
        'local government', 'public administration', 'ombudsman',
    },
    'economy': {
        'economic', 'economy', 'market', 'growth', 'inflation', 'employment',
        'trade', 'fiscal', 'budget', 'investment', 'gdp', 'revenue',
        'privatisation', 'privatization', 'competition', 'financial',
        'banking', 'tax', 'taxation', 'unemployment', 'poverty', 'social',
    },
}


# -----------------------------------------------------------------------------
# SCORING FUNCTION
# -----------------------------------------------------------------------------
def dict_score(text, term_list):
    """
    Count term list hits in text, normalized per 1,000 words.
    Uses substring match on lowercased text — catches multi-word phrases.
    Returns (raw_count, per_1000_words).
    """
    text_lower = text.lower()
    n_words    = len(text.split())
    raw        = sum(text_lower.count(term) for term in term_list)
    per1000    = (raw / n_words * 1000) if n_words > 0 else 0.0
    return raw, per1000
