"""
SkillClaw PR Agent — creates rich PRs from solver output.

Consumes SkillSave messages from a queue and:
1. Renders the trajectory into a rich PR body (no LLM needed)
2. Copies skill from private → shared brain
3. Converts video to GIF
4. Creates branch, commits, pushes, creates PR via gh

Uses git worktrees so the main working directory is never touched.
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger("pr_agent")

PROJECT_ROOT = Path(__file__).parent.parent.parent  # rlvr/agents/ → SkillClaw/

# Import the enhanced render function
sys.path.insert(0, str(PROJECT_ROOT / "brains" / "shared_brain" / "skills" / "sc-publish" / "scripts"))
from render_trajectory import render


def _solver_bot_env() -> dict:
    """Return env with solver bot token (skillclaw-bot) for gh/git commands."""
    env = os.environ.copy()
    bot_token = os.environ.get("SKILLCLAW_BOT_TOKEN_1")
    if bot_token:
        env["GH_TOKEN"] = bot_token
        env.pop("GITHUB_TOKEN", None)
    return env


def _run(cmd: str, cwd: str = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command. Uses solver bot token (skillclaw-bot) for all commands."""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True,
        cwd=cwd or str(PROJECT_ROOT), timeout=60,
        env=_solver_bot_env(),
    )
    if check and result.returncode != 0:
        logger.error(f"Command failed: {cmd}\n{result.stderr}")
    return result


async def run_pr_agent(
    skill_queue: asyncio.Queue,
    review_queue: Optional[asyncio.Queue] = None,
    timeout: float = 600,
):
    """Consume SkillSave messages and create PRs.

    Args:
        skill_queue: Queue of SkillSave objects from solver agents.
        review_queue: Queue to push completed PRs for oversight review.
        timeout: Seconds to wait for next skill before exiting.
    """
    logger.info("PR Agent started, waiting for skills...")

    while True:
        try:
            skill = await asyncio.wait_for(skill_queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.info("PR Agent: no more skills in queue, exiting.")
            break

        logger.info(f"PR Agent: processing {skill.skill_name} from {skill.agent_id}")

        try:
            await _create_pr(skill, review_queue)
        except Exception as e:
            logger.error(f"PR Agent: failed to create PR for {skill.skill_name}: {e}")

    logger.info("PR Agent finished.")


async def _create_pr(skill, review_queue):
    """Create a PR for a single skill using a git worktree."""
    import time
    name = skill.skill_name
    timestamp = time.strftime("%m%d-%H%M")
    branch = f"feat/skill-add-{name}-{timestamp}"
    private_dir = PROJECT_ROOT / "brains" / "private_brain" / f"dev-sc-{name}"

    # 1. Find the solver's skill directory
    #    The solver may choose a shorter name (e.g. "pull" instead of "pull-cube"),
    #    so scan for any dev-sc-* dir that contains a matching SKILL.md.
    if not private_dir.exists():
        private_brain = PROJECT_ROOT / "brains" / "private_brain"
        candidates = sorted(private_brain.glob("dev-sc-*/SKILL.md"))
        if candidates:
            private_dir = candidates[-1].parent
            name = private_dir.name.removeprefix("dev-sc-")
            branch = f"feat/skill-add-{name}-{timestamp}"
            skill.skill_name = name
            logger.info(f"PR Agent: found solver skill at {private_dir.name}, using name '{name}'")
        else:
            logger.error(f"PR Agent: private brain dir not found: {private_dir}")
            return

    # 2. Render trajectory (reads from disk, no git needed)
    traj_section = ""
    if skill.trajectory_path and Path(skill.trajectory_path).exists():
        try:
            traj_section = render(skill.trajectory_path)
        except Exception as e:
            logger.warning(f"PR Agent: trajectory render failed: {e}")

    # 3. Convert video to GIF (stays in demos/ on main working tree)
    gif_file = ""
    if skill.video_file:
        mp4_path = PROJECT_ROOT / "demos" / skill.video_file
        gif_name = skill.video_file.replace(".mp4", ".gif")
        gif_path = PROJECT_ROOT / "demos" / gif_name
        if mp4_path.exists():
            logger.info(f"PR Agent: converting video to GIF")
            _run(
                f'ffmpeg -i "{mp4_path}" -vf "fps=10,scale=320:-1" -y "{gif_path}" 2>/dev/null',
                check=False,
            )
            if gif_path.exists():
                gif_file = gif_name

    # 4. Create worktree for the feature branch
    #    Clean up any stale branch/worktree first
    _run(f"git branch -D {branch}", check=False)
    _run(f"git push origin --delete {branch}", check=False)

    worktree_dir = Path(tempfile.mkdtemp(prefix="skillclaw-pr-"))
    _run(f"git worktree add '{worktree_dir}' -b {branch} main")
    logger.info(f"PR Agent: created worktree at {worktree_dir}")

    try:
        # 5. Copy skill files into worktree
        shared_dir_wt = worktree_dir / "brains" / "shared_brain" / "skills" / f"sc-{name}"
        logger.info(f"PR Agent: copying {private_dir.name} → {shared_dir_wt.name}")
        shutil.copytree(private_dir, shared_dir_wt)

        # 6. Copy GIF into worktree
        if gif_file:
            gif_src = PROJECT_ROOT / "demos" / gif_file
            gif_dst = worktree_dir / "demos" / gif_file
            gif_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(gif_src, gif_dst)

        # 7. Stage, commit, push (all in worktree)
        wt = str(worktree_dir)
        _run(f"git add 'brains/shared_brain/skills/sc-{name}'", cwd=wt)
        if gif_file:
            _run(f"git add 'demos/{gif_file}'", cwd=wt)
        _run(f'git commit -m "skill: sc-{name} — {skill.description}"', cwd=wt)
        _run(f"git push -u origin {branch}", cwd=wt)

        # 8. Build PR body
        repo_result = _run("gh repo view --json nameWithOwner --jq '.nameWithOwner'", check=False)
        repo = repo_result.stdout.strip() or "lilyzhng/SkillClaw"
        commit_sha = _run("git rev-parse HEAD", cwd=wt).stdout.strip()

        gif_section = ""
        if gif_file:
            gif_url = f"https://raw.githubusercontent.com/{repo}/{commit_sha}/demos/{gif_file}"
            gif_section = f"### Demo\n\n![demo]({gif_url})\n"

        pr_body = f"""> **🤖 PR Agent** · Automated by SkillClaw

## I learned a new skill: sc-{name}

**Description:** {skill.description}

{gif_section}
{traj_section}

### Skill Files

- `brains/shared_brain/skills/sc-{name}/SKILL.md`
- `brains/shared_brain/skills/sc-{name}/scripts/main.py`
"""

        # 9. Create PR
        pr_body_file = f"/tmp/skillclaw_pr_{name}.md"
        Path(pr_body_file).write_text(pr_body)
        result = _run(
            f'gh pr create --title "I learned a new skill: {skill.description}" --body-file "{pr_body_file}"',
            cwd=wt,
        )
        pr_url = result.stdout.strip()
        logger.info(f"PR Agent: PR created — {pr_url}")
        Path(pr_body_file).unlink(missing_ok=True)

    finally:
        # 10. Clean up worktree (main working tree untouched)
        _run(f"git worktree remove '{worktree_dir}' --force", check=False)
        if worktree_dir.exists():
            shutil.rmtree(worktree_dir, ignore_errors=True)
        logger.info(f"PR Agent: cleaned up worktree")

    # 11. Clean private brain
    shutil.rmtree(private_dir, ignore_errors=True)

    # Push to review queue (GIF is still in demos/ on main working tree)
    if review_queue is not None:
        skill.pr_url = pr_url
        await review_queue.put(skill)
        logger.info(f"PR Agent: pushed to review_queue: {name}")
