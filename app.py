import streamlit as st
import matplotlib.pyplot as plt
import random

# --- PAGE CONFIG ---
st.set_page_config(page_title="Game of 21", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .taken {
        background-color: #1a1c23;
        color: #4a5568;
        border: 1px solid #2d3748;
        border-radius: 8px;
        padding: 10px;
        text-decoration: line-through;
        display: inline-block;
        margin: 5px;
        width: 45px;
        text-align: center;
    }
    .available {
        background-color: #2d3748;
        color: #63b3ed;
        border: 2px solid #4299e1;
        border-radius: 8px;
        padding: 10px;
        font-weight: bold;
        display: inline-block;
        margin: 5px;
        width: 45px;
        text-align: center;
        box-shadow: 0 0 10px rgba(66, 153, 225, 0.2);
    }
    .log-box {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 15px;
        border-radius: 10px;
        font-family: 'Consolas', monospace;
        height: 250px;
        overflow-y: auto;
    }
    .user-text { color: #00d4ff; font-weight: bold; }
    .comp-text { color: #ff7f7f; font-weight: bold; }
    .system-text { color: #f6e05e; font-style: italic; font-size: 0.9em; }
    .stAlert {
        background-color: #2d1a05;
        color: #ff9f43;
        border: 1px solid #ff9f43;
    }
    .rules-box {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-left: 3px solid #f6e05e;
        padding: 14px 16px;
        border-radius: 10px;
        font-size: 0.85em;
        line-height: 1.7;
        color: #cbd5e0;
    }
    .rules-box h4 { color: #f6e05e; margin: 0 0 8px 0; font-size: 1em; letter-spacing: 0.05em; }
    .rules-box .tip { color: #68d391; font-style: italic; margin-top: 8px; font-size: 0.92em; }
</style>
""", unsafe_allow_html=True)

# --- INITIALIZE SESSION STATE ---
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0
    st.session_state.move_labels   = ['Start']
    st.session_state.user_probs    = [50]
    st.session_state.comp_probs    = [50]
    st.session_state.player_history = ['start']
    st.session_state.take_sizes    = {'user': [], 'comp': []}
    st.session_state.action_log    = ["SYSTEM: Duel pending..."]
    st.session_state.game_over     = False
    st.session_state.winner        = None
    st.session_state.game_started  = False
    st.session_state.move_count    = 0
    st.session_state.difficulty    = 'Normal'


# ── CHART HELPER ─────────────────────────────────────────────────────────────
def compute_user_win_prob(current_idx, last_player):
    remaining = 21 - current_idx
    if remaining <= 0:
        return None

    next_player_loses = (remaining % 4 == 0)

    if last_player == 'start':
        return 50

    if last_player == 'user':
        return 85 if next_player_loses else 20
    else:
        return 20 if next_player_loses else 85


# ── GRAPHS ───────────────────────────────────────────────────────────────────
def _style_ax(ax):
    ax.set_facecolor('#111827')
    for spine in ax.spines.values():
        spine.set_color('#30363d')
        spine.set_linewidth(0.5)


def render_plots():
    plt.style.use('dark_background')

    fig = plt.figure(figsize=(9, 7.8), facecolor='#0e1117')
    gs  = fig.add_gridspec(
        2, 1,
        height_ratios=[2.2, 1],
        hspace=0.52,
        left=0.10, right=0.97,
        top=0.94,  bottom=0.09,
    )
    ax_momentum = fig.add_subplot(gs[0])
    ax_bar      = fig.add_subplot(gs[1])

    user_probs = st.session_state.user_probs
    comp_probs = st.session_state.comp_probs
    players    = st.session_state.player_history
    labels     = st.session_state.move_labels
    moves      = list(range(len(user_probs)))
    x_max      = max(len(user_probs) - 0.5, 5)

    # ── CHART 1: COMBINED MOMENTUM ───────────────────────────────────────────
    _style_ax(ax_momentum)

    ax_momentum.axhspan(50, 105, color='#00d4ff', alpha=0.04)
    ax_momentum.axhspan(-5,  50, color='#ff7f7f', alpha=0.04)
    ax_momentum.axhline(50, color='white', linewidth=1,
                        linestyle='--', alpha=0.25, zorder=2)
    ax_momentum.text(x_max - 0.05, 51.5, "Winning zone",
                     ha='right', fontsize=7, color='#00d4ff', alpha=0.45)
    ax_momentum.text(x_max - 0.05, 46,   "Losing zone",
                     ha='right', fontsize=7, color='#ff7f7f', alpha=0.45)

    if len(moves) > 1:
        ax_momentum.plot(moves, user_probs,
                         color='#00d4ff', linewidth=2.2,
                         linestyle='-', alpha=0.85, zorder=3, label='_nolegend_')

    for m, p, pl in zip(moves, user_probs, players):
        is_own   = (pl == 'user')
        is_start = (pl == 'start')
        if is_own or is_start:
            ax_momentum.scatter(m, p, color='#00d4ff', s=90, marker='o',
                                edgecolors='white', linewidths=0.8, zorder=5)
            offset = 8 if p >= 50 else -8
            va     = 'bottom' if p >= 50 else 'top'
            ax_momentum.annotate(f"{int(p)}%", xy=(m, p),
                                 xytext=(0, offset), textcoords='offset points',
                                 ha='center', va=va, fontsize=7,
                                 color='#00d4ff', alpha=0.9)
        else:
            ax_momentum.scatter(m, p, color='#00d4ff', s=40, marker='o',
                                edgecolors='#00d4ff', linewidths=0.6,
                                alpha=0.3, zorder=4)

    if len(moves) > 1:
        ax_momentum.plot(moves, comp_probs,
                         color='#ff7f7f', linewidth=2.2,
                         linestyle='--', alpha=0.85, zorder=3, label='_nolegend_')

    for m, p, pl in zip(moves, comp_probs, players):
        is_own   = (pl == 'comp')
        is_start = (pl == 'start')
        if is_own or is_start:
            ax_momentum.scatter(m, p, color='#ff7f7f', s=90, marker='s',
                                edgecolors='white', linewidths=0.8, zorder=5)
            offset = 8 if p >= 50 else -8
            va     = 'bottom' if p >= 50 else 'top'
            ax_momentum.annotate(f"{int(p)}%", xy=(m, p),
                                 xytext=(0, offset), textcoords='offset points',
                                 ha='center', va=va, fontsize=7,
                                 color='#ff7f7f', alpha=0.9)
        else:
            ax_momentum.scatter(m, p, color='#ff7f7f', s=40, marker='s',
                                edgecolors='#ff7f7f', linewidths=0.6,
                                alpha=0.3, zorder=4)

    ax_momentum.set_xlim(-0.5, x_max)
    ax_momentum.set_ylim(-8, 116)
    ax_momentum.set_yticks([0, 25, 50, 75, 100])
    ax_momentum.set_yticklabels(['0%', '25%', '50%', '75%', '100%'],
                                fontsize=8, alpha=0.7)
    ax_momentum.set_xticks(moves)
    ax_momentum.set_xticklabels(labels, fontsize=7.5, alpha=0.65)
    ax_momentum.set_title("Win Probability Momentum",
                          fontsize=11, fontweight='bold',
                          color='#e2e8f0', loc='left', pad=9)
    ax_momentum.set_ylabel("Win probability", fontsize=8, alpha=0.6)
    ax_momentum.set_xlabel("Move  ( U = your turn · C = computer's turn )",
                           fontsize=7.5, alpha=0.55)
    ax_momentum.grid(color='#30363d', linewidth=0.5, alpha=0.2)

    from matplotlib.lines import Line2D
    legend_items = [
        Line2D([0], [0], color='#00d4ff', linewidth=2.2, linestyle='-',
               marker='o', markersize=6, label='You (solid line)'),
        Line2D([0], [0], color='#ff7f7f', linewidth=2.2, linestyle='--',
               marker='s', markersize=6, label='Computer (dashed)'),
        Line2D([0], [0], color='white', linewidth=1, linestyle='--',
               alpha=0.4, label='50% — even'),
    ]
    ax_momentum.legend(handles=legend_items, loc='upper right',
                       fontsize=7.5, frameon=True, framealpha=0.25, ncol=3,
                       edgecolor='#4a5568', facecolor='#161b22')

    # ── CHART 2: CURRENT ADVANTAGE ───────────────────────────────────────────
    _style_ax(ax_bar)

    cur_user = user_probs[-1]
    cur_comp = comp_probs[-1]

    bars = ax_bar.barh(
        ['You', 'Computer'],
        [cur_user, cur_comp],
        color=['#00d4ff', '#ff7f7f'],
        height=0.42, edgecolor='none', zorder=3
    )

    for bar, val in zip(bars, [cur_user, cur_comp]):
        if val > 12:
            ax_bar.text(val - 2, bar.get_y() + bar.get_height() / 2,
                        f"{int(val)}%", va='center', ha='right',
                        fontsize=13, fontweight='bold', color='white', zorder=5)
        else:
            ax_bar.text(val + 1.5, bar.get_y() + bar.get_height() / 2,
                        f"{int(val)}%", va='center', ha='left',
                        fontsize=13, fontweight='bold', color='white', zorder=5)

    ax_bar.axvline(50, color='white', linewidth=1,
                   linestyle='--', alpha=0.35, zorder=2)
    ax_bar.text(50, -0.64, '50%', ha='center', fontsize=7.5,
                color='white', alpha=0.4)

    ax_bar.set_xlim(0, 108)
    ax_bar.set_ylim(-0.65, 1.65)
    ax_bar.set_xticks([0, 25, 50, 75, 100])
    ax_bar.set_xticklabels(['0%', '25%', '50%', '75%', '100%'],
                           fontsize=8, alpha=0.7)
    ax_bar.set_title("Current Advantage",
                     fontsize=11, fontweight='bold',
                     color='#e2e8f0', loc='left', pad=9)
    ax_bar.set_xlabel("Win probability", fontsize=8, alpha=0.6)
    ax_bar.grid(axis='x', color='#30363d', linewidth=0.5, alpha=0.2)

    return fig


# --- LOGIC ---
def process_move(chosen_nums, player):
    take_count = len(chosen_nums)
    st.session_state.current_idx += take_count
    st.session_state.take_sizes[player].append(take_count)

    color_class = "user-text" if player == "user" else "comp-text"
    log_entry = f'<span class="{color_class}">{player.upper()}: Eliminated {chosen_nums}</span>'
    st.session_state.action_log.insert(0, log_entry)

    user_prob = compute_user_win_prob(st.session_state.current_idx, player)
    if user_prob is None:
        user_prob = st.session_state.user_probs[-1]
    comp_prob = 100 - user_prob

    move_num = len(st.session_state.user_probs)
    label    = f"U{move_num}" if player == 'user' else f"C{move_num}"

    st.session_state.move_labels.append(label)
    st.session_state.user_probs.append(user_prob)
    st.session_state.comp_probs.append(comp_prob)
    st.session_state.player_history.append(player)

    if st.session_state.current_idx == 20:
        st.session_state.game_over = True
        st.session_state.winner = "User" if player == "user" else "Computer"
        st.session_state.action_log.insert(
            0, f'<span class="system-text">SYSTEM: {st.session_state.winner.upper()} '
               f'reached 20 — opponent forced to take 21.</span>')
    elif st.session_state.current_idx >= 21:
        st.session_state.game_over = True
        st.session_state.winner = "Computer" if player == "user" else "User"


def computer_turn():
    """
    Difficulty controls how often the computer plays the optimal (game-theory) move.

    Easy   → 25% chance of playing optimally; 75% purely random
    Normal → 50% chance of playing optimally; 50% random
    Hard   → 100% optimal play — computer never deviates from the winning strategy

    Optimal strategy: always leave remaining count ≡ 0 (mod 4) for the opponent.
    i.e. take  (remaining % 4)  numbers.  If that is 0 (already a losing position
    for whoever moves next = computer), take 1 as damage control.
    """
    if st.session_state.game_over:
        return

    difficulty = st.session_state.get('difficulty', 'Normal')

    # Smart-play probabilities per difficulty
    smart_prob = {'Easy': 0.25, 'Normal': 0.50, 'Hard': 1.00}[difficulty]

    curr      = st.session_state.current_idx
    remaining = 21 - curr
    max_take  = min(3, remaining - 1) if remaining > 1 else 1   # never take 21 if avoidable

    # ── Optimal (game-theory) move ───────────────────────────────────────────
    ideal_take = remaining % 4  # leaves a multiple-of-4 for opponent
    if ideal_take < 1 or ideal_take > 3:
        # Already in a losing position; take 1 as best damage control
        ideal_take = 1

    # ── Random move ──────────────────────────────────────────────────────────
    random_take = random.randint(1, max_take)

    # ── Decide based on difficulty ────────────────────────────────────────────
    take = ideal_take if random.random() < smart_prob else random_take

    # Safety clamp — never exceed board or take 21 when avoidable
    take = max(1, min(take, max_take))

    chosen = list(range(curr + 1, curr + take + 1))
    process_move(chosen, 'comp')


# --- MAIN UI ---
st.title("Game of 21")

if not st.session_state.game_started:
    c1, _ = st.columns([1, 2])
    with c1:
        starter    = st.selectbox("Choose starter:", ["User", "Computer"])
        difficulty = st.selectbox(
            "Difficulty:",
            ["Easy", "Normal", "Hard"],
            index=1,
            help="Easy = 25% optimal play · Normal = 50% · Hard = 100% (always perfect)"
        )
        if st.button("Initialize"):
            st.session_state.game_started = True
            st.session_state.difficulty   = difficulty
            if starter == "Computer":
                computer_turn()
            st.rerun()
    st.stop()

col1, col2 = st.columns([1, 1.3])

with col1:
    # ── HOW TO PLAY ──────────────────────────────────────────────────────────
    with st.expander("📖  How to Play — Rules", expanded=False):
        st.markdown("""
<div class="rules-box">
<h4>🎯 OBJECTIVE</h4>
Force your opponent to take the number <strong>21</strong>. The player who picks 21 <strong>loses</strong>.

<h4>⚙️ RULES</h4>
<div class="rule-item">▸ Numbers 1 → 21 are eliminated in order — you always start from the next available number.</div>
<div class="rule-item">▸ On your turn, take <strong>1, 2, or 3 consecutive numbers</strong> starting from the current position.</div>
<div class="rule-item">▸ Players alternate turns. You cannot skip a turn or take 0 numbers.</div>
<div class="rule-item">▸ Whoever is forced to take <strong>21</strong> loses the game.</div>
<div class="rule-item">▸ Reaching exactly <strong>20</strong> wins — your opponent must take 21.</div>

<h4>💡 HOW TO ENTER A MOVE</h4>
<div class="rule-item">▸ Type <code>5</code> to take one number (e.g. just 5).</div>
<div class="rule-item">▸ Type <code>5, 6</code> to take two consecutive numbers.</div>
<div class="rule-item">▸ Type <code>5, 6, 7</code> to take three consecutive numbers.</div>
<div class="rule-item">▸ You must always start at the <em>next available</em> number shown above the input.</div>

<div class="tip">🧠 PRO TIP: Leave your opponent at a multiple of 4 (4, 8, 12, 16, 20) — that's the winning strategy!</div>
</div>
""", unsafe_allow_html=True)

    # Difficulty badge
    diff = st.session_state.get('difficulty', 'Normal')
    diff_color = {'Easy': '#68d391', 'Normal': '#f6e05e', 'Hard': '#ff7f7f'}[diff]
    diff_pct   = {'Easy': '25%',     'Normal': '50%',     'Hard': '100%'}[diff]
    st.markdown(
        f'<div style="margin-bottom:8px;font-size:0.82em;color:{diff_color};">'
        f'⚡ Difficulty: <strong>{diff}</strong> &nbsp;|&nbsp; Smart play: {diff_pct}</div>',
        unsafe_allow_html=True
    )

    st.markdown("### BOARD")
    board_html = "".join([
        f'<div class="{"taken" if n <= st.session_state.current_idx else "available"}">{n}</div>'
        for n in range(1, 22)
    ])
    st.markdown(board_html, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### ACTION LOG")
    log_content = "<br>".join(st.session_state.action_log)
    st.markdown(f'<div class="log-box">{log_content}</div>', unsafe_allow_html=True)

    if st.session_state.game_over:
        st.markdown(f"## 🏆 WINNER: {st.session_state.winner.upper()}")
        if st.button("RESET GAME", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

with col2:
    if not st.session_state.game_over:
        next_val = st.session_state.current_idx + 1

        input_key  = f"user_move_{st.session_state.move_count}"
        user_input = st.text_input(
            f"Starting number: {next_val}",
            key=input_key,
            placeholder="Enter e.g. 1  or  1, 2, 3"
        )

        user_input_stripped = user_input.strip()
        if user_input_stripped:
            try:
                chosen = [int(x.strip()) for x in user_input_stripped.split(",") if x.strip()]
                if not (1 <= len(chosen) <= 3):
                    st.error("**MISCONDUCT:** Please take between 1 and 3 numbers.")
                elif chosen[0] != next_val or any(chosen[i] != chosen[i-1] + 1 for i in range(1, len(chosen))):
                    st.error(f"**MISCONDUCT:** Move must be consecutive numbers starting at **{next_val}**.")
                else:
                    st.session_state.move_count += 1
                    process_move(chosen, 'user')
                    if not st.session_state.game_over:
                        computer_turn()
                    st.rerun()
            except ValueError:
                st.error("**MISCONDUCT:** Please enter only valid integers separated by commas.")

    st.pyplot(render_plots())