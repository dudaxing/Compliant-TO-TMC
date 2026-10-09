"""Saved nodal weak loads for this fixed h0.5 lower-half square, in N.

Corners/intersections stay whole. This is a load ledger, not surface pressure.
Only stdlib CSV/math; no model, NPZ, force evaluation or observer import.
"""
import csv
from math import fsum,isfinite

COMPONENTS = ("total","material","regularization")
FORCE_COLUMNS = tuple(name+"_F"+axis+"_N" for name in COMPONENTS for axis in ("x","y"))
IDENTITY_COLUMNS = ("index","original_target_index","leg","d_mm","state_sha256")
CATEGORIES = ("bottom_side_interior","left_side_interior","right_side_interior",
    "physical_corner","physical_and_cut","cut_interior","body_interior")
ORIGINAL_GROUP = dict(zip(CATEGORIES,("physical_only","physical_only","physical_only",
    "physical_only","physical_and_cut","cut_only","interior")))
OLD_GROUPS = ("physical_only","cut_only","physical_and_cut","interior")

def _category(x,y,old_group):
    if not (62 <= x <= 80 and 31 <= y <= 40):
        raise ValueError("Require the recorded fixed-body rectangle [62,80]x[31,40]")
    retained = {"physical_and_cut":"physical_and_cut","cut_only":"cut_interior","interior":"body_interior"}
    if old_group in retained:
        return retained[old_group]
    if old_group != "physical_only":
        raise ValueError("Unknown closed physical/cut group")
    if y == 31 and x in (62,80):
        return "physical_corner"
    if y == 31:
        return "bottom_side_interior"
    if x == 62:
        return "left_side_interior"
    if x == 80:
        return "right_side_interior"
    raise ValueError("Recorded physical_only node does not belong to a physical square side")

def _measure(rows):
    return dict(node_count=len(rows),force_on_body_N={name:[fsum(float(row[name+"_F"+axis+"_N"])
        for row in rows) for axis in ("x","y")] for name in COMPONENTS})

def _compare(actual,expected,rows):
    errors,bounds = {},{}
    for name in COMPONENTS:
        errors[name] = [a-b for a,b in zip(actual[name],expected[name])]
        bounds[name] = [8*2.**-52*fsum(abs(float(row[name+"_F"+axis+"_N"])) for row in rows)
            for axis in ("x","y")]
        if any(abs(error) > bound for error,bound in zip(errors[name],bounds[name])):
            raise ValueError("Saved nodal load closure exceeds original node-sum roundoff bound")
    return dict(error_N=errors,roundoff_bound_N=bounds,passed=True)

def summarize_saved_workpiece_node_ledger(nodes_csv,body_metadata,*,recorded_states,
        selected_states=(0,8,13,23)):
    """Return original node text plus seven exclusive category resultants.

    body_metadata is linked_response['physics'] plus canonical_body_node_ids
    from closed model JSON. recorded_states maps index to
    {'identity': old view-summary row, 'nodal': closed nodal.json}. None selects
    all supplied records; the proposed first card supplies only four records.
    Six force strings stay untouched. math.fsum recomposes whole/old groups;
    the existing 8*eps*sum(abs(original node force)) bound has no absolute floor.
    No total=material+Hu identity or new scientific gate is imposed.
    """
    body,grid,extent = (body_metadata[key] for key in ("workpiece","grid","model_extent"))
    canonical_nodes = set(body_metadata["canonical_body_node_ids"])
    if (body["kind"],body["shape"],body["center_mm"],body["side_mm"],body["fixed_components"],
        grid["cell_size_mm"],grid["axes"],grid["origin_mm"],grid["shape_yx"],grid["extent_mm"],body_metadata["material"]["thickness_mm"],extent["kind"],extent["symmetry_axis"]) != (
        "fixed_rigid","square",[71.,40.],18.,[0,1],[.5,.5],[[1.,0.],[0.,1.]],[0.,0.],[80,168],[84.,40.],20.,"lower_half",
        {"normal":[0.,1.],"offset_mm":40.}):
        raise ValueError("This ledger supports only the recorded h0.5 fixed lower-half square")
    selected = tuple(sorted(recorded_states)) if selected_states is None else tuple(selected_states)
    if not selected or len(set(selected)) != len(selected):
        raise ValueError("Select nonempty distinct recorded state indices")
    rows_by_state = {index:[] for index in selected}
    with open(nodes_csv,newline="",encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        columns = reader.fieldnames
        if not set(IDENTITY_COLUMNS+("node_id","x_mm","y_mm","group")+FORCE_COLUMNS) <= set(columns):
            raise ValueError("Require the closed node-table identity and six force columns")
        for row in reader:
            index = int(row["index"])
            if index in rows_by_state:
                rows_by_state[index].append(row)
    states = []
    for index in selected:
        record,rows = recorded_states[index],rows_by_state[index]
        identity,nodal = record["identity"],record["nodal"]
        coordinates = dict(zip(nodal["node_ids"],nodal["coordinates_mm"]))
        seen = set()
        for row in rows:
            node = int(row["node_id"])
            if (int(row["index"]),int(row["original_target_index"]),row["leg"],float(row["d_mm"]),row["state_sha256"]) != (
                identity["index"],identity["original_target_index"],identity["leg"],identity["d_mm"],identity["state_sha256"]):
                raise ValueError("Node-table state identity differs from the closed view row")
            xy = [float(row["x_mm"]),float(row["y_mm"])]
            if node in seen or xy != coordinates[node] or not all(isfinite(float(row[key])) for key in FORCE_COLUMNS):
                raise ValueError("Require each recorded body node once, with original coordinates and finite loads")
            seen.add(node)
            category = _category(*xy,row["group"])
            if ORIGINAL_GROUP[category] != row["group"]:
                raise ValueError("Refined category disagrees with the original physical/cut group")
            row["ledger_category"] = category
        if len(rows) != 703 or seen != canonical_nodes or seen != set(coordinates):
            raise ValueError("Require all703 recorded fixed-body nodes for each selected state")
        whole = _measure(rows)
        if whole["force_on_body_N"] != nodal["summary"]["force_on_lower_body_N"] or whole["force_on_body_N"] != {
            name:[identity[name+"_body_F"+axis+"_N"] for axis in ("x","y")] for name in COMPONENTS}:
            raise ValueError("Direct node fsum must reproduce both closed whole-body records exactly")
        categories = {name:_measure([row for row in rows if row["ledger_category"] == name]) for name in CATEGORIES}
        original = {name:dict(node_count=sum(categories[category]["node_count"] for category in CATEGORIES if ORIGINAL_GROUP[category] == name),
            force_on_body_N={part:[fsum(categories[category]["force_on_body_N"][part][axis]
                for category in CATEGORIES if ORIGINAL_GROUP[category] == name) for axis in (0,1)] for part in COMPONENTS}) for name in OLD_GROUPS}
        comparison = dict(whole=_compare(whole["force_on_body_N"],nodal["summary"]["force_on_lower_body_N"],rows),old_groups={})
        for name in OLD_GROUPS:
            if original[name]["node_count"] != nodal["summary"]["groups"][name]["node_count"]:
                raise ValueError("Refined groups do not preserve the original group count")
            comparison["old_groups"][name] = _compare(original[name]["force_on_body_N"],nodal["summary"]["groups"][name]["force_on_body_N"],
                [row for row in rows if row["group"] == name])
        states.append(dict(identity={key:identity[key] for key in IDENTITY_COLUMNS},whole=whole,
            categories=categories,original_group_rollup=original,comparison=comparison,nodes=rows))
    return dict(schema_version="saved-fixed-square-node-load-ledger-1.0",selected_states=list(selected),
        original_columns=columns,force_columns=list(FORCE_COLUMNS),categories=list(CATEGORIES),states=states,
        units="N, original thickness already included",force_scope="Signed saved ON-body nodal weak loads; no corner allocation, clipping, traction or pressure",
        qualification="Selected saved-table classification and original nodal-load closure only; no full24, HP, total-boundary-force, effective-grip or pressure qualification")
