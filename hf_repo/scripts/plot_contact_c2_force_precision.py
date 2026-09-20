"""Read-only visualization of fixed-failure arithmetic; no mechanics calls."""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args();source=args.source.resolve();out=args.output.resolve()
    if out.exists():raise FileExistsError("preserve previous visualization")
    manifest=source.parent/"output_sha256.json"
    frozen=json.loads(manifest.read_text(encoding="utf-8"))
    if frozen[source.name]!=digest(source):raise ValueError("diagnostic source hash mismatch")
    record=json.loads(source.read_text(encoding="utf-8"))
    if record["mechanical_admission"]!="not_pass_unchanged":raise ValueError("unexpected diagnostic semantics")
    names=["saved_production","decimal_at_production_F_J_Hu","decimal_exact_determinant_of_production_F",
           "decimal_at_rounded_exact_F_production_Hu","decimal_at_rounded_exact_F_exact_Hu"]
    values=[float(record["variants"][name]["total"]["error_over_frozen_SF"]) for name in names]
    labels=["Original\nproduction", "120-digit stress + assembly\nproduction F / J / Hu",
            "Exact det(production F)\nproduction F / Hu",
            "Correctly rounded exact F\nproduction Hu", "Correctly rounded exact F\nexact Hu"]
    out.mkdir(parents=True)
    fig,ax=plt.subplots(figsize=(13,5.6),layout="constrained")
    ax.bar(range(5),values,color=["#ad4357"]+["#64849a"]*2+["#248870"]*2,width=.64)
    ax.set_yscale("log");ax.set_ylim(1e-16,8e-11)
    ax.set_xticks(range(5),labels,fontsize=9)
    ax.set_ylabel("Full internal-force error / frozen SF (dimensionless)")
    ax.axhline(1e-11,color="#ad4357",ls="--",lw=1.4,label="Unchanged production evaluation limit: 1e-11")
    for i,v in enumerate(values):ax.text(i,v*1.27,f"{v:.5g}",ha="center",fontsize=10)
    ax.grid(axis="y",which="major",alpha=.22);ax.set_axisbelow(True)
    ax.legend(loc="upper right",fontsize=9)
    ax.set_title("Fine mesh, d = 0.5 mm | fixed-state arithmetic attribution",loc="left",pad=36)
    ax.text(0,1.025,"Same saved split displacement and SF. First result reproduced bitwise; other bars are diagnostic counterfactuals.",
            transform=ax.transAxes,fontsize=9,color="#43505a")
    fig.supxlabel("The original path remains NOT_PASS. No new equilibrium solution, deployed kernel or consistent-tangent verification.",fontsize=10)
    fig.savefig(out/"force_precision_attribution.png",dpi=180)
    fig.savefig(out/"force_precision_attribution.svg")
    plt.close(fig)
    root=Path(__file__).resolve().parents[2]
    receipt=dict(schema="c2-arithmetic-visualization-v1",mechanical_status="not_pass_unchanged",no_new_mechanics=True,
        input_sha256={p.relative_to(root).as_posix():digest(p) for p in (source,manifest,Path(__file__))},
        plotted_series=[dict(name=n,error_over_SF=record["variants"][n]["total"]["error_over_frozen_SF"]) for n in names])
    (out/"readback.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    (out/"output_sha256.json").write_text(json.dumps({p.name:digest(p) for p in out.iterdir() if p.is_file()},indent=2)+"\n",encoding="utf-8")
    print({"output":str(out),"source_preserved":digest(source)==frozen[source.name]})


if __name__=="__main__":main()
