# Final saved nodal-force plot readiness

Status: static ready; no remaining blocker for the current frozen-data render. This is not a render pass.

- plot_saved_nodal_forces.py: 126 lines, SHA256 46a4babf1a199b9d0b5c0cc194b122bc52fc928c448e47448815b30e9d9a26f0.
- workpiece_nodal.py: 76 lines, SHA256 697e056fee1bddf4a611f2fc6e83de10747d923627b5f2d28c34eaf9a1d33ae9.
- Actual export contract read: observe_workpiece_nodal_forces.py, 195 lines, SHA256 e831d7848f19126c00e807711f614f9ae61bf5b4b0b51e3d965cea7c8995d81a.

The initial 118-line author source bde577b7 had a zip-truncation coverage gap and began its clock after heavy imports. The final source requires equal report/source state counts, starts timing before NumPy/Matplotlib/Pillow imports, and displays saved production status. These were author-stage corrections; no render or numerical phase was opened by this reviewer.

Force columns are signed force ON the body, already the negative saved internal global force. The renderer neither flips them again nor reconstructs total from components. It checks every actual accepted index and every body node in saved order; repeated targets remain distinct. One common arrow scale uses all states and all three force terms. Its units are N-to-display-mm, separate from x1 geometry. Zero arrows may be invisible; CSV retains tiny signed values.

Physical/cut edges are loaded from the saved observation. Entire symmetry-plane edges are cut edges; shared physical/cut endpoints remain explicit gold nodes without duplication. Physical-only includes physical corners, and vectors are not allocated between incident faces. Material and regularization are force terms, not solid and medium phases. Interior and cut-only rows remain in the quiver inputs and CSV.

Derived Mz is labelled in N mm with its origin and no new HP/contact qualification. The API performs ordinary rounded lever-force products then fsum; no multiplication compensation or continuous traction reconstruction is claimed. The body uses its saved reference positions, consistent with the exporter's fixed-displacement check. Mechanism displacement is only a display sum of saved arrays, not a constitutive or distance evaluation.

Saved production status is visible independently of observation-export success. Accepted N/N therefore means all cached rows and does not silently assert completed unloading for a failed partial path. The final metadata records summary/CSV/result/source SHA, all nodes/frames, common scale and x1 geometry. It verifies an empty hf_eval import closure and gives its static saved-data/import basis for zero new mechanical calls; it correctly says hooks were not monitored.

A frozen render card must bind the existing summary/CSV/result and renderer identities before launch. The viewer's final hashes detect input mutations during rendering. It currently checks historical source roles against the supplied repo; future portability can resolve those source roles using report.source_snapshots while retaining actual data SHA checks. This does not block the present same-source card.

Only source reads and AST/compile(source) were performed. No production import, render, pytest, geometry algorithm, force, tangent, consumer, HP, assembly or solver ran. Actual label readability and GIF frame retention remain for post-review of the sole render.
