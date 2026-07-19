from datetime import datetime
from types import SimpleNamespace

from flask import Blueprint, current_app, render_template

from model import Experience, Profile, Project, Skill

# Blueprint public untuk halaman portfolio dinamis.
public_portfolio_bp = Blueprint("public_portfolio_bp", __name__, template_folder="templates")


def _get_store(store_name):
    """Ambil fallback store untuk tabel tertentu dari konfigurasi aplikasi."""
    store = current_app.config.get(store_name)
    if store is None:
        store = {}
        current_app.config[store_name] = store
    return store


def _to_namespace(value):
    """Konversi dictionary fallback menjadi objek yang bisa diakses oleh Jinja."""
    if isinstance(value, dict):
        return SimpleNamespace(**value)
    return value


def _get_profile():
    """Ambil data profile pertama dari database atau store fallback."""
    try:
        profile = Profile.query.first()
        if profile:
            return profile
    except Exception:
        pass

    store = _get_store("_profile_store")
    if store:
        first_profile = next(iter(store.values()))
        return _to_namespace(first_profile)
    return None


def _get_user_id(profile):
    """Ambil user_id dari profile, baik object SQLAlchemy maupun fallback object."""
    if not profile:
        return None
    return getattr(profile, "user_id", None) or getattr(profile, "user_id", None)


def _get_skills(user_id):
    """Ambil daftar skill dari database atau store fallback."""
    if not user_id:
        return []
    try:
        return Skill.query.filter_by(user_id=user_id).all()
    except Exception:
        store = _get_store("_skill_store")
        return [
            _to_namespace(v)
            for v in store.values()
            if v.get("user_id") == user_id
        ]


def _get_experiences(user_id):
    """Ambil daftar experience dari database atau store fallback."""
    if not user_id:
        return []
    try:
        return (
            Experience.query.filter_by(user_id=user_id)
            .order_by(Experience.created_at.desc())
            .all()
        )
    except Exception:
        store = _get_store("_experience_store")
        return [
            _to_namespace(v)
            for v in sorted(
                store.values(),
                key=lambda x: x.get("created_at", ""),
                reverse=True,
            )
            if v.get("user_id") == user_id
        ]


def _get_projects(user_id):
    """Ambil daftar project dari database atau store fallback."""
    if not user_id:
        return []
    try:
        return Project.query.filter_by(user_id=user_id).all()
    except Exception:
        store = _get_store("_project_store")
        return [_to_namespace(v) for v in store.values() if v.get("user_id") == user_id]


@public_portfolio_bp.route("/", methods=["GET"])
def portfolio_index():
    """Tampilkan halaman portfolio yang memuat semua data publik dari database."""
    profile = _get_profile()
    user_id = _get_user_id(profile)
    skills = _get_skills(user_id)
    experiences = _get_experiences(user_id)
    projects = _get_projects(user_id)

    return render_template(
        "public/index.html",
        profile=profile,
        skills=skills,
        experiences=experiences,
        projects=projects,
        year=datetime.now().year,
    )
