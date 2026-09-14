# HF-2 numerical reference fixtures

These 16 NPZ files are numerical outputs from the uploaded `TMC_code.zip`,
SHA-256 `58f203ff1dba3c64c64d5fa2de12d4bdd3a711be69ee83a4ddd3335680e3eb08`,
evaluated by MATLAB R2023b. The copied reference index binds every NPZ to its
hash and the frozen validation spec hash. No MATLAB source or executable is
included. MAT filenames and wrapper metadata in that index describe the
external provenance archive; those files are not runtime dependencies.

Cases are the 12 predefined nonaffine rectangular elements and four small
meshes. Local arrays use BL, BR, TR, TL with interleaved ux, uy; canonical
nodes/elements are x-fast from bottom to top. Source permutations are explicit.
Quadrature is xi slow, eta fast. The MATLAB residual/tangent are obtained from
the unchanged source assembler. Material and regularization components are
isolated by separate kr=0 and material-factor=0 calls. J, F, second Piola
stress, and weighted material energy come from a labeled external postprocessor.

The tests need only the Python HF package and these numerical arrays. The
standalone `scripts/validate_hf2.py` additionally saves all 160 predefined
directional finite differences and independent analytic checks. These results
test implementation and source-code agreement, not physical contact accuracy.
