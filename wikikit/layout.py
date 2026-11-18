"""Where a MOC or a template lives. The kit's naming rules, overridable per entry in wiki.config.json.

An existing wiki often has names the rules would not produce (acronyms such as `MOC_ML_Sport`, or a field MOC
called `MOC_Strength_Conditioning` while the display title is "Strength & Conditioning"). Computing the name by
hand from the rule would then create a second MOC next to the real one, so the tools ask here.
"""
from .config import vault_path


def moc_stem(cfg, field, subfield=None):
    """File stem of a field MOC (no subfield) or of a sub-MOC. `moc_names` wins over the rule."""
    key = "%s/%s" % (field, subfield) if subfield else field
    if key in cfg.get("moc_names", {}):
        return cfg["moc_names"][key]
    if subfield:  # kebab-case to Title_Case_Underscore
        return "MOC_" + "_".join(w.capitalize() for w in subfield.split("-"))
    title = cfg.get("field_titlecase_map", {}).get(field) or "_".join(w.capitalize() for w in field.split("-"))
    return "MOC_" + title.replace(" ", "_")  # the display title verbatim (WIKI_SCHEMA.md, Field MOC name)


def moc_relpath(cfg, field, subfield=None):
    """Path of the MOC relative to the wiki root, with forward slashes."""
    stem = moc_stem(cfg, field, subfield)
    return "fields/%s/%s.md" % (field, stem) if subfield else "fields/%s.md" % stem


def template_path(root, cfg, kind):
    """Template file for a note kind (paper, concept, method, book, chapter, moc, submoc)."""
    name = cfg.get("template_names", {}).get(kind, kind + ".md")
    return vault_path(root, cfg) / cfg.get("templates_dir", "templates") / name
